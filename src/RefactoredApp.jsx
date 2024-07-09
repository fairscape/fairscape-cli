import React, { useState } from "react";
import { Container, Row } from "react-bootstrap";
import SidebarComponent from "./components/Sidebar";
import { AppContainer } from "./components/StyledComponents";
import commandsData from "./data/commandsData";
import MainContentComponent from "./components/MainContent";

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

  return (
    <AppContainer>
      <SidebarComponent
        commands={commandsData}
        selectedCommand={selectedCommand}
        handleCommandSelect={handleCommandSelect}
      />
      <MainContentComponent
        commands={commandsData}
        selectedCommand={selectedCommand}
        selectedSubCommand={selectedSubCommand}
        selectedSubSubCommand={selectedSubSubCommand}
        options={options}
        output={output}
        rocratePath={rocratePath}
        schemaFile={schemaFile}
        handleSubCommandSelect={handleSubCommandSelect}
        handleSubSubCommandSelect={handleSubSubCommandSelect}
        handleOptionChange={handleOptionChange}
        handleRocratePathChange={handleRocratePathChange}
        handleSchemaFileChange={handleSchemaFileChange}
        handleSubmit={handleSubmit}
        isExecuteDisabled={isExecuteDisabled}
      />
    </AppContainer>
  );
}

export default App;
