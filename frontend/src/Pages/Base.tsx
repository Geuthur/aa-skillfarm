// React
import { Outlet } from "react-router-dom";

// Third Party
import { Col } from "react-bootstrap";

import { ErrorBoundary } from "@/Components/Loader";
import AuthLeftMenuAsync from "@/Menu/AuthLeftMenuAsync";
import AuthRightMenuAsync from "@/Menu/AuthRightMenuAsync";

/**
 * BasePage component that provides the layout for AllianceAuth
 */
export const BasePage = () => {
  return (
    <>
      <AuthLeftMenuAsync />
      <AuthRightMenuAsync />
      <Col>
        <div className="aa-section mt-4 tw-priority">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </Col>
    </>
  );
};

export default BasePage;
