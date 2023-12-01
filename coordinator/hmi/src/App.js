import { useState, useEffect } from "react";

import WaterTank from "./components/WaterTank";
import VerticalPipe from "./components/VerticalPipe";
import Readout from "./components/Readout";

function toggleCallback(newValue, setState) {
  setState(newValue ? 1 : 0);
}

function setManualControlRequest(value) {
  fetch(`/manual?s=${value ? 1 : 0}`, {
    method: 'POST'
  })
    .then((response) => {})
}

function App() {
  const secondsBetweenUpdate = 1;

  const [manualControl, setManualControl] = useState(0);
  const [timeOfDay, setTimeOfDay] = useState(0);
  const [waterLevelHigh, setWaterLevelHigh] = useState(0);
  const [gateOpen, setGateOpen] = useState(0);
  const [pumpOn, setPumpOn] = useState(0);

  useEffect(() => {
    function updateData() {
      // for production:
      fetch("/update")
        .then((response) => response.json())
        .then((json) => {
          console.log("updating data with vvv");
          console.log(json);
          setManualControl(json.manualControl);
          setTimeOfDay(json.timeOfDay);
          setWaterLevelHigh(json.waterLevelHigh);
          setGateOpen(json.gateOpen);
          setPumpOn(json.pumpOn);
        })

      // for testing:
      //const updateData = {
      //  manualControl: 0,
      //  timeOfDay: 0,
      //  waterLevelHigh: 0,
      //  gateOpen: 0,
      //  pumpOn: 0
      //}
      //setManualControl(updateData.manualControl);
      //setTimeOfDay(updateData.timeOfDay);
      //setWaterLevelHigh(updateData.waterLevelHigh);
      //setGateOpen(updateData.gateOpen);
      //setPumpOn(updateData.pumpOn);
    }

    updateData()
    const interval = setInterval(() => updateData(), secondsBetweenUpdate * 1000);
    return () => {
      clearInterval(interval);
    }
  }, []);

  return (
    <div className="App">
      <header>
        PSH HMI
      </header>
      <WaterTank pos={[200, 100]} />
      <VerticalPipe pos={[400, 125]} draining={gateOpen !== 0}/>
      <VerticalPipe pos={[400, 225]} lifting={pumpOn !== 0}/>
      <WaterTank pos={[500, 100]} />

      <Readout pos={[100, 50]} name="CONTROL STYLE" value={manualControl} onLabel="MANUAL" offLabel="AUTO" onColor="red" offColor="green" withToggle toggleCallback={(v) => {setManualControlRequest(v); toggleCallback(v, setManualControl)}}/>
      <Readout pos={[100, 400]} name="TIME OF DAY" value={timeOfDay} onLabel="DAY" offLabel="NIGHT" onColor="white" offColor="gray" />
      <Readout pos={[200, 400]} name="WATER LEVEL" value={waterLevelHigh} onLabel="HIGH" offLabel="LOW" onColor="red" offColor="green" />
      <Readout pos={[300, 400]} name="GATE" value={gateOpen} onLabel="OPEN" offLabel="CLOSED" onColor="green" offColor="red" withToggle={manualControl} toggleCallback={(v) => {toggleCallback(v, setGateOpen)}}/>
      <Readout pos={[400, 400]} name="PUMP" value={pumpOn} onLabel="ON" offLabel="OFF" onColor="green" offColor="red" withToggle={manualControl} toggleCallback={(v) => {toggleCallback(v, setPumpOn)}}/>
    </div>
  );
}

export default App;
