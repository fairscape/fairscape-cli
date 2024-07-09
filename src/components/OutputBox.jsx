import React from "react";
import { OutputBox } from "./StyledComponents";

function OutputBoxComponent({ output }) {
  return (
    <>
      <h4>Output:</h4>
      <OutputBox>{output}</OutputBox>
    </>
  );
}

export default OutputBoxComponent;
