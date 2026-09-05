function SuggestedQuestion({ children, onClick }) {
    return (
      <button
        className="suggested-question"
        onClick={onClick}
      >
        {children}
      </button>
    );
  }
  
  export default SuggestedQuestion;