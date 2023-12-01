function WaterTank(props) {
    return (
        <div className="WaterTank" style={{ width: "200px", height: "200px", border: "1px solid black", backgroundColor: "blue", position: "absolute", top: props.pos[0], left: props.pos[1] }}>
            
        </div>
    )
}

export default WaterTank;