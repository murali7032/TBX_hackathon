function InsightPreview() {
    return (
      <section className="dashboard-section insight-preview">
  
        <div className="section-header">
          <div>
            <p className="eyebrow">AI INSIGHT</p>
            <h2>Something you should know</h2>
          </div>
  
          <span className="ai-symbol">✦</span>
        </div>
  
        <div className="insight-content">
  
          <div className="insight-alert">
            ⚠
          </div>
  
          <div>
            <h3>
              Your food spending is higher than usual.
            </h3>
  
            <p>
              You've spent ₹12,400 on food this month,
              around 27% more than your typical monthly
              spending.
            </p>
  
            <button className="text-button">
              See all insights →
            </button>
          </div>
  
        </div>
  
      </section>
    );
  }
  
  export default InsightPreview;