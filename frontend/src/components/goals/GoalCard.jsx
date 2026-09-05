function GoalCard({
    name,
    saved,
    target,
    percentage,
    targetDate,
  }) {
    const remaining = Math.max(
      target - saved,
      0
    );
  
    return (
      <div className="goal-card">
  
        <div className="goal-card-header">
  
          <div>
            <p className="eyebrow">
              GOAL
            </p>
  
            <h3>{name}</h3>
          </div>
  
          <span className="goal-percentage">
            {percentage}%
          </span>
  
        </div>
  
        <div className="goal-progress">
  
          <div
            className="goal-progress-bar"
            style={{
              width: `${percentage}%`,
            }}
          />
  
        </div>
  
        <div className="goal-amounts">
  
          <div>
            <strong>
              ₹{saved.toLocaleString("en-IN")}
            </strong>
  
            <span>saved</span>
          </div>
  
          <div>
            <strong>
              ₹{target.toLocaleString("en-IN")}
            </strong>
  
            <span>target</span>
          </div>
  
        </div>
  
        <div className="goal-bottom">
  
          <span>
            ₹{remaining.toLocaleString("en-IN")}
            {" "}remaining
          </span>
  
          <span>
            Target: {targetDate}
          </span>
  
        </div>
  
      </div>
    );
  }
  
  export default GoalCard;