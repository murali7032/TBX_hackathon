function GoalsOverview({ goals = [] }) {

    return (
      <section className="dashboard-section">
  
        <div className="section-header">
  
          <div>
            <p className="eyebrow">
              GOALS
            </p>
  
            <h2>
              Your goals
            </h2>
          </div>
  
          <button className="text-button">
            View all →
          </button>
  
        </div>
  
  
        {goals.length === 0 ? (
  
          <div className="section-empty">
            <p>No goals yet.</p>
          </div>
  
        ) : (
  
          <div className="goals-list">
  
            {goals.map((goal) => (
  
              <div
                className="goal-item"
                key={goal.id}
              >
  
                <div className="goal-header">
  
                  <strong>
                    {goal.name}
                  </strong>
  
                  <span>
                    {goal.percentage}%
                  </span>
  
                </div>
  
  
                <div className="progress-track">
  
                  <div
                    className="progress-bar"
                    style={{
                      width: `${goal.percentage}%`,
                    }}
                  />
  
                </div>
  
  
                <div className="goal-footer">
  
                  <span>
                    ₹
                    {Number(goal.saved_amount)
                      .toLocaleString("en-IN")}
                    {" "}saved
                  </span>
  
                  <span>
                    ₹
                    {Number(goal.remaining)
                      .toLocaleString("en-IN")}
                    {" "}remaining
                  </span>
  
                </div>
  
              </div>
  
            ))}
  
          </div>
  
        )}
  
      </section>
    );
  }
  
  
  export default GoalsOverview;