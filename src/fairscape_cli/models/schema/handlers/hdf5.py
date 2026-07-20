from typing import List, Optional

import h5py
import pandas as pd
from frictionless import Resource, describe

from fairscape_models.schema import Schema, Property

from fairscape_cli.models.schema.core import (
    SchemaHandler,
    ValidationErrorRecord,
    frictionless_error_to_record,
    frictionless_type_to_json_schema,
    register_handler,
    SOURCE_TYPE_KEY,
)
from fairscape_cli.models.schema.handlers.tabular import build_frictionless_schema


def dataset_to_dataframe(dataset: h5py.Dataset) -> pd.DataFrame:
    """Convert an HDF5 dataset to a pandas DataFrame"""
    data = dataset[()]

    if dataset.dtype.fields:  # Structured array
        return pd.DataFrame(data)
    elif len(dataset.shape) > 1:  # Multi-dimensional array
        n_cols = dataset.shape[1]
        columns = [f"column_{i}" for i in range(n_cols)]
        return pd.DataFrame(data, columns=columns)
    else:  # 1D array
        return pd.DataFrame(data, columns=['value'])


@register_handler('h5', 'hdf5')
class HDF5Handler(SchemaHandler):
    extensions = ('h5', 'hdf5')

    def infer(self, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> Schema:
        properties = {}

        with h5py.File(filepath, 'r') as f:
            def process_group(group, parent_path=""):
                for key, item in group.items():
                    path = f"{parent_path}/{key}" if parent_path else key

                    if isinstance(item, h5py.Dataset):
                        try:
                            df = dataset_to_dataframe(item)
                            resource = describe(df)

                            columns = {}
                            for i, field in enumerate(resource.schema.fields):
                                json_schema_type = frictionless_type_to_json_schema(field.type)
                                extra = {}
                                if json_schema_type != field.type:
                                    extra[SOURCE_TYPE_KEY] = field.type
                                columns[field.name] = Property(
                                    type=json_schema_type,
                                    description=field.description or f"Column {field.name}",
                                    index=i,
                                    **extra,
                                )

                            # The int index is a placeholder required by the
                            # canonical Property index validator; validation
                            # keys datasets on the path, never this index.
                            properties[path] = Property(
                                type='object',
                                index=len(properties),
                                description=f"Dataset at {path}",
                                properties=columns,
                                **{'hdf5-path': path},
                            )

                        except Exception as e:
                            print(f"Warning: Could not process dataset {path}: {str(e)}")

                    elif isinstance(item, h5py.Group):
                        process_group(item, path)

            process_group(f)

        return self.new_schema(
            name=name,
            description=description,
            guid=guid,
            properties=properties,
            required=list(properties.keys()),
        )

    def validate(self, schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
        errors = []

        with h5py.File(filepath, 'r') as f:
            for path, prop in schema.properties.items():
                if prop.type != 'object' or not prop.properties:
                    continue
                try:
                    dataset = f[path]
                    if isinstance(dataset, h5py.Dataset):
                        df = dataset_to_dataframe(dataset)
                        frictionless_schema = build_frictionless_schema(prop.properties)
                        resource = Resource(data=df, schema=frictionless_schema)
                        report = resource.validate()

                        for task in report.tasks:
                            for error in task.errors:
                                # Skip string type errors: h5py returns bytes
                                # for string data, which frictionless flags as
                                # a type mismatch against string fields.
                                if (hasattr(error, 'type') and error.type == 'type-error' and
                                    hasattr(error, 'note') and 'type is "string' in error.note):
                                    continue

                                errors.append(frictionless_error_to_record(error, path=path))

                except KeyError:
                    errors.append(ValidationErrorRecord(
                        message=f"Dataset {path} not found",
                        failed_keyword="required",
                        path=path,
                    ))
                except Exception as e:
                    errors.append(ValidationErrorRecord(
                        message=f"Error validating dataset {path}: {str(e)}",
                        failed_keyword="format",
                        path=path,
                    ))

        return errors
