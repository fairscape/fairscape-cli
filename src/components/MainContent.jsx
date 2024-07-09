import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import CommandForm from "./CommandForm";
import OutputBoxComponent from "./OutputBox";
import {
  MainContent,
  SmallerCol,
  LargerCol,
  SidebarItem,
} from "./StyledComponents";

function MainContentComponent({
  commands,
  selectedCommand,
  selectedSubCommand,
  selectedSubSubCommand,
  options,
  output,
  rocratePath,
  schemaFile,
  handleSubCommandSelect,
  handleSubSubCommandSelect,
  handleOptionChange,
  handleRocratePathChange,
  handleSchemaFileChange,
  handleSubmit,
  isExecuteDisabled,
}) {
  return (
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
            <CommandForm
              commands={commands}
              selectedCommand={selectedCommand}
              selectedSubCommand={selectedSubCommand}
              selectedSubSubCommand={selectedSubSubCommand}
              options={options}
              rocratePath={rocratePath}
              schemaFile={schemaFile}
              handleOptionChange={handleOptionChange}
              handleRocratePathChange={handleRocratePathChange}
              handleSchemaFileChange={handleSchemaFileChange}
              handleSubmit={handleSubmit}
              isExecuteDisabled={isExecuteDisabled}
            />
          </LargerCol>
        </Row>
        <Row>
          <Col>
            <OutputBoxComponent output={output} />
          </Col>
        </Row>
      </Container>
    </MainContent>
  );
}

export default MainContentComponent;
