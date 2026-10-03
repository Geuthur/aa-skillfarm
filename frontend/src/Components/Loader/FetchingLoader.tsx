// Styles
import styles from "./FetchingLoader.module.css";

interface LoaderProps {
  message?: string;
  className?: string;
}

export const FetchingLoader = ({ message, className = "" }: LoaderProps = {}) => {
  return (
    <div className={`${styles["flex-container-loader"]} ${className}`}>
      <div
        className={`spinner-border text-info ${styles["spinner-size"]}`}
        role="status"
      >
        <span className="visually-hidden">Loading...</span>
      </div>
      {message && (
        <span>
          {message}
        </span>
      )}
    </div>
  );
};

export default FetchingLoader;
