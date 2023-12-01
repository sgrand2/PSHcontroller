function VerticalPipe(props) {
    let content = undefined;
    const contentStyle = { width: "50px", height: "100px", fontSize: "60px", position: "relative", top: "13px"};
    if (props.draining && !props.lifting) {
        content = <span style={contentStyle}>&#8595;</span>
    } else if (props.lifting && !props.draining) {
        content = <span style={contentStyle}>&#8593;</span>;
    }

    return (
        <div className="VerticalPipe" style={{ width: "50px", height: "100px", border: "1px solid black", backgroundColor: "blue", position: "absolute", top: props.pos[0], left: props.pos[1] }}>
            {content}
        </div>
    )
}

export default VerticalPipe;