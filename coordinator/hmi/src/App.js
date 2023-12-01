import { useState, useEffect } from "react";

import WaterTank from "./components/WaterTank";
import VerticalPipe from "./components/VerticalPipe";
import Readout from "./components/Readout";

function gateToggleCallback(newValue, setState) {
  console.log("setting gate open to: " + newValue);
  setState(newValue ? 1 : 0);
}

function pumpToggleCallback(newValue, setState) {
  console.log("setting pump running to: " + newValue);
  setState(newValue ? 1 : 0);
}

function App() {
  const secondsBetweenUpdate = 5;

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
          setTimeOfDay(json.timeOfDay);
          setWaterLevelHigh(json.waterLevelHigh);
          setGateOpen(json.gateOpen);
          setPumpOn(json.pumpOn);
        })

      // for testing:
      //const updateData = {
      //  timeOfDay: 0,
      //  waterLevelHigh: 0,
      //  gateOpen: 0,
      //  pumpOn: 0
      //}
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

      <Readout pos={[100, 400]} name="TIME OF DAY" value={timeOfDay} onLabel="DAY" offLabel="NIGHT" onColor="white" offColor="gray" />
      <Readout pos={[200, 400]} name="WATER LEVEL" value={waterLevelHigh} onLabel="HIGH" offLabel="LOW" onColor="red" offColor="green" />
      <Readout pos={[300, 400]} name="GATE" value={gateOpen} onLabel="OPEN" offLabel="CLOSED" onColor="green" offColor="red" withToggle toggleCallback={(v) => {gateToggleCallback(v, setGateOpen)}}/>
      <Readout pos={[400, 400]} name="PUMP" value={pumpOn} onLabel="ON" offLabel="OFF" onColor="green" offColor="red" withToggle toggleCallback={(v) => {pumpToggleCallback(v, setPumpOn)}}/>
    </div>
  );
}

export default App;
