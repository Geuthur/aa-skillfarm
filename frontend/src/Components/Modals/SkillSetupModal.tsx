// React
import React, { useState } from "react";

// Third Party
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";

// Styles
import styles from "./SkillSetupModal.module.css";

import { fetchSkillSetup, updateSkillSetup } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Modals/BaseModal";
import type { ModalData } from "@/Components/Modals/BaseModal";

interface SkillSetupModalProps {
  characterId: number | null;
  onClose: () => void;
}

export const SkillSetupModal: React.FC<SkillSetupModalProps> = ({ characterId, onClose }) => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  // null = untouched, the saved skillset is shown
  const [editedSkills, setEditedSkills] = useState<string[] | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.SkillSetup(characterId),
    queryFn: () => (characterId ? fetchSkillSetup(characterId) : Promise.reject("No ID")),
    enabled: !!characterId,
  });

  const selectedSkills = editedSkills ?? data?.skillset ?? [];

  const handleClose = () => {
    setEditedSkills(null);
    onClose();
  };

  const mutation = useMutation({
    mutationFn: () => {
      if (!characterId) throw new Error("No character selected");
      return updateSkillSetup(characterId, selectedSkills);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.CharactersRoot });
      queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
      queryClient.invalidateQueries({ queryKey: queryKeys.CharacterDetail(characterId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.SkillSetup(characterId) });
      handleClose();
    },
  });

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
    title: data ? `${data.character_name} — Farm Skillset Setup` : "Farm Skillset Setup",
    buttonText: "Save Skillset",
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
        await mutation.mutateAsync();
      }}
    >
      <div>
        <p className="aa-panel text-secondary small mb-3">
          Select which skills trigger extraction readiness alerts when reaching Level 5.
        </p>

        {isLoading && (
          <div className={styles["loading-state"]}>
            Loading skills...
          </div>
        )}

        {data && (
          <div>
            <div className={`${styles["search-wrapper"]}`}>
              <Search
                size={16}
                className={styles["search-icon"]}
              />
              <input
                type="text"
                className={`sf-search-input ${styles["search-input"]}`}
                placeholder="Filter available skills..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className={styles["selection-summary"]}>
              Selected for extraction: <strong className={styles["selection-count"]}>{selectedSkills.length}</strong> skills
            </div>

            <div
              className={styles["skill-list"]}
            >
              {filteredSkills.length === 0 ? (
                <div className={styles["empty-state"]}>
                  No matching skills found.
                </div>
              ) : (
                <div className={styles["skill-grid"]}>
                  {filteredSkills.map((skill) => {
                    const isSelected = selectedSkills.includes(skill);
                    return (
                      <label
                        key={skill}
                        className={`${styles["skill-option"]} ${isSelected ? styles["skill-option-selected"] : ""}`}
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
