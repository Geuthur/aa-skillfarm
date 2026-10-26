// React
import React, { useState } from "react";

// Third Party
import { Search } from "lucide-react";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/SkillSetupModal.module.css";

import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import type { ModalData } from "@/Components/Base/BaseModal";

import { useSaveSkillSetup, useSkillSetup } from "@/Components/Modals/Hooks";
interface SkillSetupModalProps {
  characterId: number | null;
  onClose: () => void;
}

export const SkillSetupModal: React.FC<SkillSetupModalProps> = ({ characterId, onClose }) => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState("");
  // null = untouched, the saved skillset is shown
  const [editedSkills, setEditedSkills] = useState<string[] | null>(null);

  const { data, isLoading } = useSkillSetup(characterId);

  const selectedSkills = editedSkills ?? data?.skillset ?? [];

  const handleClose = () => {
    setEditedSkills(null);
    onClose();
  };

  const mutation = useSaveSkillSetup(characterId, handleClose);

  if (!characterId) return null;

  const handleToggleSkill = (skill: string) => {
    setEditedSkills(
      selectedSkills.includes(skill) ? selectedSkills.filter((s) => s !== skill) : [...selectedSkills, skill]
    );
  };

  const filteredSkills = (data?.available_skills || []).filter((s) =>
    s.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const modalData: ModalData = {
    modal_id: "skillsetup-modal",
    title: data
      ? t("{{character}} — Farm Skillset Setup", { character: data.character_name })
      : t("Farm Skillset Setup"),
    buttonText: t("Save Skillset"),
    color: "primary",
    url: "",
  };

  return (
    <BaseModal
      data={modalData}
      showModal={!!characterId}
      setShowModal={(show) => {
        if (!show) handleClose();
      }}
      isPending={mutation.isPending}
      size={ModalSize.large}
      onApprove={async () => {
        await mutation.mutateAsync(selectedSkills);
      }}
    >
      <div>
        <p className="aa-panel text-secondary small mb-3">
          {t("Select which skills trigger extraction readiness alerts when reaching Level 5.")}
        </p>

        {isLoading && (
          <div className={`${styles["loading-state"]} text-center`}>
            {t("Loading skills…")}
          </div>
        )}

        {data && (
          <div>
            <div className={`${styles["search-wrapper"]} position-relative`}>
              <Search
                size={16}
                className={`${styles["search-icon"]} position-absolute`}
              />
              <input
                type="text"
                className={`sf-search-input ${styles["search-input"]} w-100`}
                placeholder={t("Filter available skills…")}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className={styles["selection-summary"]}>
              {t("Selected for extraction:")} <strong className={styles["selection-count"]}>{selectedSkills.length}</strong> {t("skills")}
            </div>

            <div
              className={`${styles["skill-list"]} p-2`}
            >
              {filteredSkills.length === 0 ? (
                <div className={`${styles["empty-state"]} text-center`}>
                  {t("No matching skills found.")}
                </div>
              ) : (
                <div className={`${styles["skill-grid"]} d-grid gap-1`}>
                  {filteredSkills.map((skill) => {
                    const isSelected = selectedSkills.includes(skill);
                    return (
                      <label
                        key={skill}
                        className={`${styles["skill-option"]} d-flex align-items-center gap-2 ${isSelected ? styles["skill-option-selected"] : ""}`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSkill(skill)}
                        />
                        <span
                          className={`${styles["skill-label"]} ${isSelected ? styles["skill-label-selected"] : ""}`}
                        >
                          {skill}
                        </span>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </BaseModal>
  );
};

export default SkillSetupModal;
