function formatCurrency(value) {
    return `₹${Number(value || 0).toLocaleString("en-IN")}`;
  }
  
  
  function PurchaseAnalysisCard({ data }) {
  
    const {
      purchase_price,
      current_balance,
      remaining_balance,
      monthly_income,
      monthly_expenses,
      monthly_savings,
      affordable,
    } = data;
  
  
    return (
      <div className="purchase-analysis-card">
  
        <div className="purchase-card-header">
          <div>
            <span className="purchase-card-label">
              Purchase Analysis
            </span>
  
            <h3>
              {formatCurrency(purchase_price)}
            </h3>
          </div>
  
          <div
            className={
              affordable
                ? "purchase-status affordable"
                : "purchase-status caution"
            }
          >
            {affordable ? "✓ Affordable" : "⚠ Caution"}
          </div>
        </div>
  
  
        <div className="purchase-card-grid">
  
          <div className="purchase-metric">
            <span>Current balance</span>
            <strong>
              {formatCurrency(current_balance)}
            </strong>
          </div>
  
  
          <div className="purchase-metric">
            <span>After purchase</span>
            <strong>
              {formatCurrency(remaining_balance)}
            </strong>
          </div>
  
  
          <div className="purchase-metric">
            <span>Monthly income</span>
            <strong>
              {formatCurrency(monthly_income)}
            </strong>
          </div>
  
  
          <div className="purchase-metric">
            <span>Monthly savings</span>
            <strong>
              {formatCurrency(monthly_savings)}
            </strong>
          </div>
  
        </div>
  
  
        <div className="purchase-card-footer">
  
          Monthly expenses:
  
          <strong>
            {formatCurrency(monthly_expenses)}
          </strong>
  
        </div>
  
      </div>
    );
  }
  
  
  export default PurchaseAnalysisCard;