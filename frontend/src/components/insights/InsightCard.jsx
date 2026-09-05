function InsightCard({
    type,
    title,
    description,
    action,
  }) {
    return (
      <div className="insight-card-full">
        <div className={`insight-type ${type}`}>
          {type === "warning" && "⚠"}
          {type === "positive" && "✓"}
          {type === "goal" && "◎"}
          {type === "opportunity" && "✦"}
        </div>
  
        <div className="insight-card-body">
          <h3>{title}</h3>
  
          <p>{description}</p>
  
          {action && (
            <button className="text-button">
              {action} →
            </button>
          )}
        </div>
      </div>
    );
  }
  
  export default InsightCard;