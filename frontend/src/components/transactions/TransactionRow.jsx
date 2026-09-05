function TransactionRow({
    date,
    description,
    category,
    amount,
    type,
  }) {
    const isIncome = type === "income";
  
    return (
      <div className="transaction-row">
  
        <div className="transaction-date">
          {date}
        </div>
  
        <div className="transaction-description">
          <strong>{description}</strong>
          <span>{category}</span>
        </div>
  
        <div
          className={`transaction-amount ${
            isIncome ? "income" : "expense"
          }`}
        >
          {isIncome ? "+" : "-"}₹
          {amount.toLocaleString("en-IN")}
        </div>
  
      </div>
    );
  }
  
  export default TransactionRow;