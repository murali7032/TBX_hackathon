import StatCard from "./StatCard";

function FinancialSummary({ finance }) {
  return (
    <section className="financial-summary">

      <StatCard
        label="Balance"
        value={`₹${Number(finance.balance).toLocaleString("en-IN")}`}
        description="Available now"
        icon="₹"
      />

      <StatCard
        label="Income"
        value={`₹${Number(finance.income).toLocaleString("en-IN")}`}
        description="This month"
        icon="↑"
      />

      <StatCard
        label="Expenses"
        value={`₹${Number(finance.expenses).toLocaleString("en-IN")}`}
        description="This month"
        icon="↓"
      />

      <StatCard
        label="Savings"
        value={`₹${Number(finance.savings).toLocaleString("en-IN")}`}
        description={`${finance.savings_rate}% savings rate`}
        icon="◎"
      />

    </section>
  );
}

export default FinancialSummary;