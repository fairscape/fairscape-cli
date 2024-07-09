import React from "react";
import { Sidebar, SidebarItem } from "./StyledComponents";

function SidebarComponent({ commands, selectedCommand, handleCommandSelect }) {
  return (
    <Sidebar>
      <h3 style={{ marginBottom: "20px", color: "#1976D2" }}>FAIRSCAPE CLI</h3>
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
  );
}

export default SidebarComponent;
