import builtins
import pathlib
from typing import Set, Dict, Any
import pandas as pd
import numpy as np

from .config import TrackerConfig
from .utils import normalize_path, is_trackable_path


class IOCapture:
    """Captures file I/O operations during code execution."""
    
    def __init__(self, config: TrackerConfig = None):
        self.config = config or TrackerConfig()
        self.inputs: Set[str] = set()
        self.outputs: Set[str] = set()
        self.original_functions: Dict[str, Any] = {}
        self.captured_variables: Dict[str, Any] = {}
    
    def _should_track(self, filepath) -> bool:
        """Check if filepath should be tracked."""
        return is_trackable_path(filepath, self.config.excluded_patterns)
    
    def _normalize_path(self, filepath) -> str:
        """Normalize filepath to absolute string."""
        return normalize_path(filepath)
    
    def patch_open(self):
        """Patch builtin open function to track file I/O."""
        if not self.config.track_builtins:
            return
            
        original_open = builtins.open
        self.original_functions['builtins.open'] = original_open
        
        capture = self
        
        def tracked_open(file, mode='r', *args, **kwargs):
            if capture._should_track(file):
                normalized = capture._normalize_path(file)
                if 'r' in mode:
                    capture.inputs.add(normalized)
                if any(m in mode for m in ['w', 'a', 'x']):
                    capture.outputs.add(normalized)
            return original_open(file, mode, *args, **kwargs)
        
        builtins.open = tracked_open
    
    def patch_pathlib(self):
        """Patch pathlib methods to track file I/O."""
        if not self.config.track_pathlib:
            return
            
        original_path_open = pathlib.Path.open
        original_read_text = pathlib.Path.read_text
        original_read_bytes = pathlib.Path.read_bytes
        original_write_text = pathlib.Path.write_text
        original_write_bytes = pathlib.Path.write_bytes
        
        self.original_functions['pathlib.Path.open'] = original_path_open
        self.original_functions['pathlib.Path.read_text'] = original_read_text
        self.original_functions['pathlib.Path.read_bytes'] = original_read_bytes
        self.original_functions['pathlib.Path.write_text'] = original_write_text
        self.original_functions['pathlib.Path.write_bytes'] = original_write_bytes
        
        capture = self
        
        def tracked_path_open(self, mode='r', *args, **kwargs):
            if capture._should_track(self):
                normalized = capture._normalize_path(self)
                if 'r' in mode:
                    capture.inputs.add(normalized)
                if any(m in mode for m in ['w', 'a', 'x']):
                    capture.outputs.add(normalized)
            return original_path_open(self, mode, *args, **kwargs)
        
        def tracked_read_text(self, *args, **kwargs):
            if capture._should_track(self):
                capture.inputs.add(capture._normalize_path(self))
            return original_read_text(self, *args, **kwargs)
        
        def tracked_read_bytes(self, *args, **kwargs):
            if capture._should_track(self):
                capture.inputs.add(capture._normalize_path(self))
            return original_read_bytes(self, *args, **kwargs)
        
        def tracked_write_text(self, *args, **kwargs):
            if capture._should_track(self):
                capture.outputs.add(capture._normalize_path(self))
            return original_write_text(self, *args, **kwargs)
        
        def tracked_write_bytes(self, *args, **kwargs):
            if capture._should_track(self):
                capture.outputs.add(capture._normalize_path(self))
            return original_write_bytes(self, *args, **kwargs)
        
        pathlib.Path.open = tracked_path_open
        pathlib.Path.read_text = tracked_read_text
        pathlib.Path.read_bytes = tracked_read_bytes
        pathlib.Path.write_text = tracked_write_text
        pathlib.Path.write_bytes = tracked_write_bytes
    
    def patch_pandas(self):
        """Patch pandas methods to track file I/O."""
        if not self.config.track_pandas:
            return
            
        original_read_csv = pd.read_csv
        original_read_excel = pd.read_excel
        original_read_parquet = pd.read_parquet
        original_read_json = pd.read_json
        original_to_csv = pd.DataFrame.to_csv
        original_to_excel = pd.DataFrame.to_excel
        original_to_parquet = pd.DataFrame.to_parquet
        original_to_json = pd.DataFrame.to_json
        
        self.original_functions['pd.read_csv'] = original_read_csv
        self.original_functions['pd.read_excel'] = original_read_excel
        self.original_functions['pd.read_parquet'] = original_read_parquet
        self.original_functions['pd.read_json'] = original_read_json
        self.original_functions['pd.DataFrame.to_csv'] = original_to_csv
        self.original_functions['pd.DataFrame.to_excel'] = original_to_excel
        self.original_functions['pd.DataFrame.to_parquet'] = original_to_parquet
        self.original_functions['pd.DataFrame.to_json'] = original_to_json
        
        capture = self
        
        def tracked_read_csv(filepath_or_buffer, *args, **kwargs):
            if capture._should_track(filepath_or_buffer):
                capture.inputs.add(capture._normalize_path(filepath_or_buffer))
            return original_read_csv(filepath_or_buffer, *args, **kwargs)
        
        def tracked_read_excel(io, *args, **kwargs):
            if capture._should_track(io):
                capture.inputs.add(capture._normalize_path(io))
            return original_read_excel(io, *args, **kwargs)
        
        def tracked_read_parquet(path, *args, **kwargs):
            if capture._should_track(path):
                capture.inputs.add(capture._normalize_path(path))
            return original_read_parquet(path, *args, **kwargs)
        
        def tracked_read_json(path_or_buf, *args, **kwargs):
            if capture._should_track(path_or_buf):
                capture.inputs.add(capture._normalize_path(path_or_buf))
            return original_read_json(path_or_buf, *args, **kwargs)
        
        def tracked_to_csv(df_self, path_or_buf=None, *args, **kwargs):
            if path_or_buf and capture._should_track(path_or_buf):
                capture.outputs.add(capture._normalize_path(path_or_buf))
            return original_to_csv(df_self, path_or_buf, *args, **kwargs)
        
        def tracked_to_excel(df_self, excel_writer, *args, **kwargs):
            if capture._should_track(excel_writer):
                capture.outputs.add(capture._normalize_path(excel_writer))
            return original_to_excel(df_self, excel_writer, *args, **kwargs)
        
        def tracked_to_parquet(df_self, path, *args, **kwargs):
            if capture._should_track(path):
                capture.outputs.add(capture._normalize_path(path))
            return original_to_parquet(df_self, path, *args, **kwargs)
        
        def tracked_to_json(df_self, path_or_buf=None, *args, **kwargs):
            if path_or_buf and capture._should_track(path_or_buf):
                capture.outputs.add(capture._normalize_path(path_or_buf))
            return original_to_json(df_self, path_or_buf, *args, **kwargs)
        
        pd.read_csv = tracked_read_csv
        pd.read_excel = tracked_read_excel
        pd.read_parquet = tracked_read_parquet
        pd.read_json = tracked_read_json
        pd.DataFrame.to_csv = tracked_to_csv
        pd.DataFrame.to_excel = tracked_to_excel
        pd.DataFrame.to_parquet = tracked_to_parquet
        pd.DataFrame.to_json = tracked_to_json
    
    def patch_numpy(self):
        """Patch numpy methods to track file I/O."""
        if not self.config.track_numpy:
            return

        original_load = np.load
        original_save = np.save
        original_loadtxt = np.loadtxt
        original_savetxt = np.savetxt

        self.original_functions['np.load'] = original_load
        self.original_functions['np.save'] = original_save
        self.original_functions['np.loadtxt'] = original_loadtxt
        self.original_functions['np.savetxt'] = original_savetxt

        capture = self

        def tracked_load(file, *args, **kwargs):
            if capture._should_track(file):
                capture.inputs.add(capture._normalize_path(file))
            return original_load(file, *args, **kwargs)

        def tracked_save(file, arr, *args, **kwargs):
            if capture._should_track(file):
                capture.outputs.add(capture._normalize_path(file))
            return original_save(file, arr, *args, **kwargs)

        def tracked_loadtxt(fname, *args, **kwargs):
            if capture._should_track(fname):
                capture.inputs.add(capture._normalize_path(fname))
            return original_loadtxt(fname, *args, **kwargs)

        def tracked_savetxt(fname, X, *args, **kwargs):
            if capture._should_track(fname):
                capture.outputs.add(capture._normalize_path(fname))
            return original_savetxt(fname, X, *args, **kwargs)

        np.load = tracked_load
        np.save = tracked_save
        np.loadtxt = tracked_loadtxt
        np.savetxt = tracked_savetxt

    def patch_matplotlib(self):
        """Patch matplotlib methods to track file I/O."""
        if not self.config.track_matplotlib:
            return

        try:
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
        except ImportError:
            return

        original_plt_savefig = plt.savefig
        original_figure_savefig = Figure.savefig

        self.original_functions['plt.savefig'] = original_plt_savefig
        self.original_functions['Figure.savefig'] = original_figure_savefig

        capture = self

        def tracked_plt_savefig(fname, *args, **kwargs):
            if capture._should_track(fname):
                capture.outputs.add(capture._normalize_path(fname))
            return original_plt_savefig(fname, *args, **kwargs)

        def tracked_figure_savefig(self, fname, *args, **kwargs):
            if capture._should_track(fname):
                capture.outputs.add(capture._normalize_path(fname))
            return original_figure_savefig(self, fname, *args, **kwargs)

        plt.savefig = tracked_plt_savefig
        Figure.savefig = tracked_figure_savefig
    
    def restore_all(self):
        """Restore all original functions."""
        builtins.open = self.original_functions.get('builtins.open', builtins.open)

        if 'pathlib.Path.open' in self.original_functions:
            pathlib.Path.open = self.original_functions['pathlib.Path.open']
            pathlib.Path.read_text = self.original_functions['pathlib.Path.read_text']
            pathlib.Path.read_bytes = self.original_functions['pathlib.Path.read_bytes']
            pathlib.Path.write_text = self.original_functions['pathlib.Path.write_text']
            pathlib.Path.write_bytes = self.original_functions['pathlib.Path.write_bytes']

        if 'pd.read_csv' in self.original_functions:
            pd.read_csv = self.original_functions['pd.read_csv']
            pd.read_excel = self.original_functions['pd.read_excel']
            pd.read_parquet = self.original_functions['pd.read_parquet']
            pd.read_json = self.original_functions['pd.read_json']
            pd.DataFrame.to_csv = self.original_functions['pd.DataFrame.to_csv']
            pd.DataFrame.to_excel = self.original_functions['pd.DataFrame.to_excel']
            pd.DataFrame.to_parquet = self.original_functions['pd.DataFrame.to_parquet']
            pd.DataFrame.to_json = self.original_functions['pd.DataFrame.to_json']

        if 'np.load' in self.original_functions:
            np.load = self.original_functions['np.load']
            np.save = self.original_functions['np.save']
            np.loadtxt = self.original_functions['np.loadtxt']
            np.savetxt = self.original_functions['np.savetxt']

        if 'plt.savefig' in self.original_functions:
            try:
                import matplotlib.pyplot as plt
                from matplotlib.figure import Figure
                plt.savefig = self.original_functions['plt.savefig']
                Figure.savefig = self.original_functions['Figure.savefig']
            except ImportError:
                pass

    def __enter__(self):
        self.patch_open()
        self.patch_pathlib()
        self.patch_pandas()
        self.patch_numpy()
        self.patch_matplotlib()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_all()
        return False
