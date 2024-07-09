import React from "react";
import { Form } from "react-bootstrap";
import {
  StyledForm,
  StyledFormGroup,
  StyledFormControl,
  StyledButton,
} from "./StyledComponents";

function CommandForm({
  commands,
  selectedCommand,
  selectedSubCommand,
  selectedSubSubCommand,
  options,
  rocratePath,
  schemaFile,
  handleOptionChange,
  handleRocratePathChange,
  handleSchemaFileChange,
  handleSubmit,
  isExecuteDisabled,
}) {
  const renderOptions = () => {
    let currentOptions = commands[selectedCommand];
    if (selectedSubCommand) {
      currentOptions = currentOptions[selectedSubCommand];
    }
    if (selectedSubSubCommand) {
      currentOptions = currentOptions[selectedSubSubCommand];
    }

    if (
      !currentOptions ||
      (!currentOptions.options && !currentOptions.required)
    ) {
      return null;
    }

    const allOptions = currentOptions.options || currentOptions.required;

    return (
      <>
        {selectedCommand === "rocrate" && (
          <Form.Group className="mb-3">
            <Form.Label style={{ color: "#ff9800" }}>ROCRATE_PATH *</Form.Label>
            <Form.Control
              type="text"
              value={rocratePath}
              onChange={handleRocratePathChange}
              required
            />
          </Form.Group>
        )}
        {selectedCommand === "schema" && (
          <Form.Group className="mb-3">
            <Form.Label style={{ color: "#ff9800" }}>SCHEMA_FILE *</Form.Label>
            <Form.Control
              type="text"
              value={schemaFile}
              onChange={handleSchemaFileChange}
              required
            />
          </Form.Group>
        )}
        {allOptions.map((option) => (
          <Form.Group key={option} className="mb-3">
            <Form.Label
              style={{
                color:
                  currentOptions.required &&
                  currentOptions.required.includes(option)
                    ? "#ff9800"
                    : "inherit",
              }}
            >
              {option}{" "}
              {currentOptions.required &&
              currentOptions.required.includes(option)
                ? "*"
                : ""}
            </Form.Label>
            <Form.Control
              type="text"
              value={options[option] || ""}
              onChange={(e) => handleOptionChange(option, e.target.value)}
              required={
                currentOptions.required &&
                currentOptions.required.includes(option)
              }
            />
          </Form.Group>
        ))}
      </>
    );
  };

  return (
    <StyledForm onSubmit={handleSubmit}>
      {renderOptions()}
      <StyledButton type="submit" disabled={isExecuteDisabled()}>
        Execute
      </StyledButton>
    </StyledForm>
  );
}

export default CommandForm;
