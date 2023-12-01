import Switch from "react-switch";

function Readout(props) {
    const w = props.withToggle ? "300px" : "200px";
    const gtc = props.withToggle ? "auto auto auto" : "auto auto";
    const toggleElement = props.withToggle ? (<div style={{ width: "100px" }}><Switch onChange={props.toggleCallback} checked={props.value !== 0} /></div>) : undefined
    const bgc = props.value === 0 ? props.offColor : props.onColor;

    return (
        <div className="Readout" style={{ border: "1px solid black", backgroundColor: bgc, height: "50px", width: w, position: "absolute", top: props.pos[0], left: props.pos[1], display: "grid", gridTemplateColumns: gtc }}>
            <h4 style={{ width: "100px", margin: "0px" }}>{props.name}</h4>
            <h5 style={{ width: "100px", margin: "0px" }}>{props.value === 0 ? props.offLabel : props.onLabel}</h5>
            {toggleElement}
        </div>
    )
}

export default Readout;