// React
import React from "react";

// Third Party
// AA Skillfarm
import { BaseModal, ModalSize } from "aa-geuthur-react";
import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

/**
 * Shows the full ESI error message of a character audit.
 * Rendered on top of other modals (e.g. the alts modal) without closing them.
 */
export interface AdministrationErrorModalProps {
  show: boolean;
  onHide: () => void;
  characterName: string;
  status: string;
  errorMessage?: string | null;
}

export const AdministrationErrorModal: React.FC<AdministrationErrorModalProps> = ({
  show,
  onHide,
  characterName,
  status,
  errorMessage = null,
}) => {
  const { t } = useTranslation();

  const message =
    errorMessage ||
    (status === "token_error"
      ? t("The ESI token is invalid or expired. Re-add the character.")
      : t("No error message available."));

  return (
    <BaseModal
      show={show}
      onHide={onHide}
      title={t("ESI Error Details")}
      size={ModalSize.large}
    >
      <div className="d-flex align-items-center gap-2 mb-3">
        <span className="fw-semibold">{characterName}</span>
        <Badge bg={status === "token_error" ? "warning" : "danger"} text={status === "token_error" ? "dark" : undefined}>
          {status}
        </Badge>
      </div>
      <pre className="text-break text-wrap mb-0" data-testid="administration-error-message">
        {message}
      </pre>
    </BaseModal>
  );
};

export default AdministrationErrorModal;
