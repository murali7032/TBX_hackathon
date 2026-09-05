const spendingData = [
    {
      category: "Food",
      amount: 12400,
      percentage: 45,
    },
    {
      category: "Shopping",
      amount: 9800,
      percentage: 36,
    },
    {
      category: "Transport",
      amount: 5200,
      percentage: 24,
    },
    {
      category: "Entertainment",
      amount: 4100,
      percentage: 16,
    },
  ];
  
  function SpendingOverview() {
    return (
      <section className="dashboard-section">
  
        <div className="section-header">
          <div>
            <p className="eyebrow">SPENDING</p>
            <h2>This month's spending</h2>
          </div>
  
          <button className="text-button">
            View all →
          </button>
        </div>
  
        <div className="spending-list">
  
          {spendingData.map((item) => (
            <div
              className="spending-item"
              key={item.category}
            >
              <div className="spending-info">
                <span>{item.category}</span>
  
                <strong>
                  ₹{item.amount.toLocaleString("en-IN")}
                </strong>
              </div>
  
              <div className="progress-track">
                <div
                  className="progress-bar"
                  style={{
                    width: `${item.percentage}%`,
                  }}
                />
              </div>
            </div>
          ))}
  
        </div>
      </section>
    );
  }
  
  export default SpendingOverview;