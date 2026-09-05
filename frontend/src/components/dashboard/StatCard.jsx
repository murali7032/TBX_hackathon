function StatCard({ label, value, description, icon }) {
    return (
      <div className="stat-card">
        <div className="stat-card-top">
          <span className="stat-icon">{icon}</span>
  
          <span className="stat-label">
            {label}
          </span>
        </div>
  
        <h3>{value}</h3>
  
        {description && (
          <p>{description}</p>
        )}
      </div>
    );
  }
  
  export default StatCard;