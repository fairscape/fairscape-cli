import React, { useState } from "react";
import { Container, Form, Button, Row, Col } from "react-bootstrap";
import styled from "styled-components";
const { exec } = window.require("child_process");

// Styled components for a sleeker look
const accentColor = "#1976D2";
const accentColorHover = "#2196F3";

const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background-color: #121212;
  color: #ffffff;
`;

const Sidebar = styled.div`
  width: 200px;
  background-color: #000000;
  padding: 20px;
`;

const MainContent = styled.div`
  flex-grow: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
`;

const SidebarItem = styled.div`
  padding: 10px;
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 4px;
  &:hover {
    background-color: #282828;
  }
  ${(props) =>
    props.active &&
    `
    background-color: ${accentColor};
    &:hover {
      background-color: ${accentColorHover};
    }
  `}
`;

const StyledForm = styled(Form)`
  background-color: #282828;
  padding: 20px;
  border-radius: 8px;
  overflow-y: auto;
  max-height: calc(100vh - 200px); // Adjust this value as needed
`;

const StyledFormGroup = styled(Form.Group)`
  margin-bottom: 15px;
`;

const StyledFormControl = styled(Form.Control)`
  background-color: #3e3e3e;
  border: none;
  color: #ffffff;
  &:focus {
    background-color: #3e3e3e;
    color: #ffffff;
    box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.25);
  }
`;

const StyledButton = styled(Button)`
  background-color: ${accentColor};
  border: none;
  &:hover,
  &:focus,
  &:active {
    background-color: ${accentColorHover};
  }
`;

const OutputBox = styled.pre`
  background-color: #282828;
  color: ${accentColor};
  padding: 15px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-wrap: break-word;
  flex-grow: 1;
  overflow-y: auto;
  margin-top: 20px;
`;

const SmallerCol = styled(Col)`
  flex: 0 0 20%;
  max-width: 20%;
`;

const LargerCol = styled(Col)`
  flex: 0 0 60%;
  max-width: 60%;
`;

const commands = {
  rocrate: {
    create: {
      create: {
        options: [
          "guid",
          "name",
          "organization-name",
          "project-name",
          "description",
          "keywords",
        ],
        required: [
          "name",
          "organization-name",
          "project-name",
          "description",
          "keywords",
        ],
      },
    },
    add: {
      dataset: {
        options: [
          "guid",
          "name",
          "url",
          "author",
          "version",
          "date-published",
          "description",
          "keywords",
          "data-format",
          "source-filepath",
          "destination-filepath",
          "used-by",
          "derived-from",
          "schema",
          "associated-publication",
          "additional-documentation",
        ],
        required: [
          "name",
          "author",
          "version",
          "date-published",
          "description",
          "keywords",
          "data-format",
          "source-filepath",
          "destination-filepath",
        ],
      },
      software: {
        options: [
          "guid",
          "name",
          "author",
          "version",
          "description",
          "keywords",
          "file-format",
          "url",
          "source-filepath",
          "destination-filepath",
          "date-modified",
          "used-by-computation",
          "associated-publication",
          "additional-documentation",
        ],
        required: [
          "name",
          "author",
          "version",
          "description",
          "keywords",
          "file-format",
          "source-filepath",
          "destination-filepath",
          "date-modified",
        ],
      },
    },
    register: {
      computation: {
        options: [
          "guid",
          "name",
          "run-by",
          "command",
          "date-created",
          "description",
          "keywords",
          "used-software",
          "used-dataset",
          "generated",
        ],
        required: ["name", "run-by", "date-created", "description", "keywords"],
      },
      dataset: {
        options: [
          "guid",
          "name",
          "url",
          "author",
          "version",
          "date-published",
          "description",
          "keywords",
          "data-format",
          "filepath",
          "used-by",
          "derived-from",
          "schema",
          "associated-publication",
          "additional-documentation",
        ],
        required: [
          "name",
          "author",
          "version",
          "date-published",
          "description",
          "keywords",
          "data-format",
          "filepath",
        ],
      },
      software: {
        options: [
          "guid",
          "name",
          "author",
          "version",
          "description",
          "keywords",
          "file-format",
          "url",
          "date-modified",
          "filepath",
          "used-by-computation",
          "associated-publication",
          "additional-documentation",
        ],
        required: [
          "name",
          "author",
          "version",
          "description",
          "keywords",
          "file-format",
        ],
      },
    },
  },
  schema: {
    "create-tabular": {
      create: {
        options: ["name", "description", "guid", "separator", "header"],
        required: ["name", "description", "separator"],
      },
    },
    "add-property": {
      string: {
        options: ["name", "index", "description", "value-url", "pattern"],
        required: ["name", "index", "description"],
      },
      number: {
        options: ["name", "index", "description", "value-url"],
        required: ["name", "index", "description"],
      },
      integer: {
        options: ["name", "index", "description", "value-url"],
        required: ["name", "index", "description"],
      },
      array: {
        options: [
          "name",
          "index",
          "description",
          "value-url",
          "items-datatype",
          "min-items",
          "max-items",
          "unique-items",
        ],
        required: ["name", "index", "description", "items-datatype"],
      },
      boolean: {
        options: ["name", "index", "description", "value-url"],
        required: ["name", "index", "description"],
      },
    },
    validate: {
      validate: {
        options: ["data", "schema"],
        required: ["data", "schema"],
      },
    },
  },
};

function App() {
  const [selectedCommand, setSelectedCommand] = useState("");
  const [selectedSubCommand, setSelectedSubCommand] = useState("");
  const [selectedSubSubCommand, setSelectedSubSubCommand] = useState("");
  const [options, setOptions] = useState({});
  const [output, setOutput] = useState("");
  const [rocratePath, setRocratePath] = useState("");
  const [schemaFile, setSchemaFile] = useState("");

  const handleCommandSelect = (command) => {
    setSelectedCommand(command);
    setSelectedSubCommand("");
    setSelectedSubSubCommand("");
    setOptions({});
    setRocratePath("");
    setSchemaFile("");

    // Auto-select subcommand if there's only one
    const subCommands = Object.keys(commands[command]);
    if (subCommands.length === 1) {
      handleSubCommandSelect(subCommands[0]);
    }
  };

  const handleSubCommandSelect = (subCommand) => {
    setSelectedSubCommand(subCommand);
    setSelectedSubSubCommand("");
    setOptions({});

    // Auto-select sub-subcommand if there's only one
    const subSubCommands = Object.keys(commands[selectedCommand][subCommand]);
    if (subSubCommands.length === 1) {
      handleSubSubCommandSelect(subSubCommands[0]);
    }
  };

  const handleSubSubCommandSelect = (subSubCommand) => {
    setSelectedSubSubCommand(subSubCommand);
    setOptions({});
  };

  const handleOptionChange = (option, value) => {
    setOptions({ ...options, [option]: value });
  };

  const handleRocratePathChange = (e) => {
    setRocratePath(e.target.value);
  };

  const handleSchemaFileChange = (e) => {
    setSchemaFile(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    let command = `fairscape-cli ${selectedCommand} ${selectedSubCommand}`;
    if (selectedSubSubCommand) {
      command += ` ${selectedSubSubCommand}`;
    }

    Object.entries(options).forEach(([key, value]) => {
      if (value) {
        command += ` --${key} "${value}"`;
      }
    });

    // Add ROCRATE_PATH for rocrate commands
    if (selectedCommand === "rocrate") {
      command += ` "${rocratePath}"`;
    }

    // Add SCHEMA_FILE for schema commands
    if (selectedCommand === "schema") {
      command += ` "${schemaFile}"`;
    }

    exec(command, (error, stdout, stderr) => {
      if (error) {
        setOutput(`Error: ${error.message}`);
        return;
      }
      if (stderr) {
        setOutput(`stderr: ${stderr}`);
        return;
      }
      setOutput(stdout);
    });
  };

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

  const isExecuteDisabled = () => {
    let currentOptions = commands[selectedCommand];
    if (selectedSubCommand) {
      currentOptions = currentOptions[selectedSubCommand];
    }
    if (selectedSubSubCommand) {
      currentOptions = currentOptions[selectedSubSubCommand];
    }

    if (!currentOptions || !currentOptions.required) {
      return true;
    }

    const requiredFieldsFilled = currentOptions.required.every(
      (option) => options[option] && options[option].trim() !== ""
    );

    // Check if ROCRATE_PATH is filled for rocrate commands
    const rocratePathFilled =
      selectedCommand !== "rocrate" ||
      (rocratePath && rocratePath.trim() !== "");

    // Check if SCHEMA_FILE is filled for schema commands
    const schemaFileFilled =
      selectedCommand !== "schema" || (schemaFile && schemaFile.trim() !== "");

    return !(requiredFieldsFilled && rocratePathFilled && schemaFileFilled);
  };

  return (
    <AppContainer>
      <Sidebar>
        <h3 style={{ marginBottom: "20px", color: accentColor }}>
          FAIRSCAPE CLI
        </h3>
        {Object.keys(commands).map((command) => (
          <SidebarItem
            key={command}
            active={selectedCommand === command}
            onClick={() => handleCommandSelect(command)}
          >
            {command}
          </SidebarItem>
        ))}
      </Sidebar>
      <MainContent>
        <Container
          fluid
          style={{ height: "100%", display: "flex", flexDirection: "column" }}
        >
          <Row style={{ flexGrow: 1, minHeight: 0 }}>
            <SmallerCol>
              {selectedCommand && (
                <div>
                  <h5 style={{ marginBottom: "15px" }}>Subcommands</h5>
                  {Object.keys(commands[selectedCommand]).map((subCommand) => (
                    <SidebarItem
                      key={subCommand}
                      active={selectedSubCommand === subCommand}
                      onClick={() => handleSubCommandSelect(subCommand)}
                    >
                      {subCommand}
                    </SidebarItem>
                  ))}
                </div>
              )}
            </SmallerCol>
            <SmallerCol>
              {selectedSubCommand &&
                commands[selectedCommand][selectedSubCommand] &&
                typeof commands[selectedCommand][selectedSubCommand] ===
                  "object" && (
                  <div>
                    <h5 style={{ marginBottom: "15px" }}>Options</h5>
                    {Object.keys(
                      commands[selectedCommand][selectedSubCommand]
                    ).map((subSubCommand) => (
                      <SidebarItem
                        key={subSubCommand}
                        active={selectedSubSubCommand === subSubCommand}
                        onClick={() => handleSubSubCommandSelect(subSubCommand)}
                      >
                        {subSubCommand}
                      </SidebarItem>
                    ))}
                  </div>
                )}
            </SmallerCol>
            <LargerCol>
              <StyledForm onSubmit={handleSubmit}>
                {renderOptions()}
                <StyledButton type="submit" disabled={isExecuteDisabled()}>
                  Execute
                </StyledButton>
              </StyledForm>
            </LargerCol>
          </Row>
          <Row>
            <Col>
              <h4>Output:</h4>
              <OutputBox>{output}</OutputBox>
            </Col>
          </Row>
        </Container>
      </MainContent>
    </AppContainer>
  );
}

export default App;
