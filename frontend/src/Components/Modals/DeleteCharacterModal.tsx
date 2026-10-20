// React
import React from "react";

// Third Party
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/DeleteCharacterModal.module.css";

import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import type { ModalData } from "@/Components/Base/BaseModal";

export interface DeletableCharacter {
  character_id: number;
  character_name: string;
  corporation_name?: string;
  corporation_ticker?: string;
  portrait_url?: string;
}

interface DeleteCharacterModalProps {
  character: DeletableCharacter | null;
  showModal: boolean;
  setShowModal: (show: boolean) => void;
  onConfirm: () => Promise<void> | void;
  isPending?: boolean;
}

export const DeleteCharacterModal: React.FC<DeleteCharacterModalProps> = ({
  character,
  showModal,
  setShowModal,
  onConfirm,
  isPending = false,
}) => {
  const { t } = useTranslation();

  if (!character) return null;

  const modalData: ModalData = {
    modal_id: "delete-character-modal",
    title: t("Delete Character"),
    buttonText: t("Delete Character"),
    color: "danger",
    url: "",
  };

  return (
    <BaseModal
      data={modalData}
      showModal={showModal}
      setShowModal={setShowModal}
      isPending={isPending}
      size={ModalSize.medium}
      onApprove={async () => {
        await onConfirm();
      }}
    >
      <div className="py-2 aa-panel">
        <div className="d-flex align-items-center gap-3 mb-3">
          <img
            src={character.portrait_url}
            alt={character.character_name}
            className={`rounded-circle border ${styles["avatar"]}`}
          />
          <div>
            <h5 className="mb-0 text-white">{character.character_name}</h5>
            <small className="text-secondary">
              {character.corporation_name} [{character.corporation_ticker}]
            </small>
          </div>
        </div>

        <p className="text-light mb-3">
          {t("Are you sure you want to delete this character?")}
        </p>

        <div className="alert alert-danger mb-0 small d-flex align-items-start gap-2">
          <i className="fas fa-exclamation-triangle mt-1" />
          <div>
            {t(
              "This action will permanently delete this character and its training configuration from Skillfarm."
            )}
          </div>
        </div>
      </div>
    </BaseModal>
  );
};

export default DeleteCharacterModal;
