import { useEffect, useState } from "react";
import { apiGet } from "../api";

function Banks() {
  const [banks, setBanks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet("/api/banks")
      .then(setBanks)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <h1>Banks</h1>
      <p className="page-sub">Institutional bank directory from the TBX Finance ledger.</p>
      {error && <p className="error-text">{error}</p>}
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            {banks.map((bank) => (
              <tr key={bank.bank_code}>
                <td>{bank.bank_code}</td>
                <td>{bank.bank_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Banks;
