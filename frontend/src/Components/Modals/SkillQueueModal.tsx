// React
import React from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { Clock, Sparkles } from "lucide-react";

// Styles
import styles from "./SkillQueueModal.module.css";

import { fetchCharacterDetail } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Modals/BaseModal";
import type { ModalData } from "@/Components/Modals/BaseModal";
import { QueueEntryProgress } from "@/Components/QueueEntryProgress";
import { TrainingProgressBar } from "@/Components/TrainingProgressBar";

interface SkillQueueModalProps {
  characterId: number | null;
  onClose: () => void;
}

export const SkillQueueModal: React.FC<SkillQueueModalProps> = ({ characterId, onClose }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.CharacterDetail(characterId),
    queryFn: () => (characterId ? fetchCharacterDetail(characterId) : Promise.reject("No ID")),
    enabled: !!characterId,
  });

  if (!characterId) return null;

  const modalData: ModalData = {
    modal_id: "skillqueue-modal",
    title: data ? `${data.character.character_name} — Skill Queue` : "Skill Queue",
    url: "",
  };

  return (
    <BaseModal
      data={modalData}
      showModal={!!characterId}
      setShowModal={(show) => {
        if (!show) onClose();
      }}
      size={ModalSize.large}
    >
      <div>
        {isLoading && (
          <div className={styles["loading-state"]}>
            Loading queue details...
          </div>
        )}

        {error && (
          <div className={styles["error-state"]}>
            Failed to load skill queue.
          </div>
        )}

        {data && (
          <div>
            {/* Header info */}
            <div className="d-flex align-items-center gap-3 mb-3">
              {data.character.portrait_url && (
                <img
                  src={data.character.portrait_url}
                  alt={data.character.character_name}
                  className={`rounded-circle ${styles["avatar"]}`}
                />
              )}
              <div>
                <h5 className="mb-0 text-white">{data.character.character_name}</h5>
                <small className="text-secondary">
                  {data.character.corporation_name} [{data.character.corporation_ticker}]
                </small>
              </div>
            </div>

            {/* Summary Stats */}
            <div
              className={styles["summary-grid"]}
            >
              <div className={`aa-panel ${styles["summary-card"]}`}>
                <div className={styles["summary-label"]}>Total SP</div>
                <div className={styles["summary-value"]}>
                  {(data.character.total_sp / 1_000_000).toFixed(2)}M
                </div>
              </div>

              <div className={`aa-panel ${styles["summary-card"]}`}>
                <div className={styles["summary-label"]}>Queue State</div>
                <div className={styles["summary-value-sm"]}>
                  {data.character.is_training ? (
                    <span className={styles["status-active"]}>Active</span>
                  ) : (
                    <span className={styles["status-paused"]}>Paused / Empty</span>
                  )}
                </div>
              </div>

              <div className={`aa-panel ${styles["summary-card"]}`}>
                <div className={styles["summary-label"]}>Ready Extractions</div>
                <div className={styles["summary-value-amber"]}>
                  {data.character.extractions_ready_count}
                </div>
              </div>
            </div>

            {/* Current training progress */}
            <div className={`aa-panel ${styles["training-panel"]}`}>
              <TrainingProgressBar
                isTraining={data.character.is_training}
                currentSkill={data.character.current_training_skill}
                trainingStartDate={data.character.training_start_date}
                trainingFinishDate={data.character.training_finish_date}
                queueFinishDate={data.character.queue_finish_date}
                queuePausedAcknowledged={data.character.queue_paused_acknowledged}
                progressPercent={data.character.progress_percent}
              />
            </div>

            {/* Queue List */}
            <h6 className={styles["section-title"]}>
              Active Training Queue ({data.skillqueue.length})
            </h6>

            {data.skillqueue.length === 0 ? (
              <div className={`aa-panel ${styles["empty-state"]}`}>
                No skills in queue. Training is inactive.
              </div>
            ) : (
              <div className="sf-table-container">
                <table className="sf-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Skill</th>
                      <th>Level</th>
                      <th>Progress</th>
                      <th>Finish Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.skillqueue.map((entry) => (
                      <tr key={`${entry.skill_id}-${entry.queue_position}`}>
                        <td>{entry.queue_position + 1}</td>
                        <td className={styles["skill-name"]}>{entry.skill_name}</td>
                        <td>{entry.finished_level_roman}</td>
                        <td className={styles["progress-cell"]}>
                          {entry.is_active ? (
                            <QueueEntryProgress
                              startDate={entry.start_date}
                              finishDate={entry.finish_date}
                              fallbackPercent={entry.progress_percent}
                            />
                          ) : (
                            <span className={styles["muted-text"]}>
                              -
                            </span>
                          )}
                        </td>
                        <td className={styles["date-cell"]}>
                          {entry.finish_date || "-"}
                        </td>
                        <td>
                          {entry.is_active ? (
                            <span className="sf-badge-training">
                              <Clock size={12} />
                              <span>Training</span>
                            </span>
                          ) : entry.is_extractable ? (
                            <span className="sf-badge-extraction-pending">
                              <Sparkles size={12} />
                              <span>Ready</span>
                            </span>
                          ) : (
                            <span className={styles["muted-text"]}>
                              Queued
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Farmed Skills in Setup */}
            {data.farmed_skills.length > 0 && (
              <div className={styles["farmed-section"]}>
                <h6 className={styles["section-title"]}>
                  Configured Farm Skills ({data.farmed_skills.length})
                </h6>
                <div className="sf-table-container">
                  <table className="sf-table">
                    <thead>
                      <tr>
                        <th>Skill</th>
                        <th>Trained Level</th>
                        <th>SP</th>
                        <th>Extraction Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.farmed_skills.map((skill) => (
                        <tr key={skill.skill_id}>
                          <td className={styles["skill-name"]}>{skill.skill_name}</td>
                          <td>Level {skill.trained_level}</td>
                          <td>{skill.skillpoints.toLocaleString()} SP</td>
                          <td>
                            {skill.is_extractable ? (
                              <span className="sf-badge-extraction-pending">
                                <Sparkles size={12} />
                                <span>Extractable (Lvl 5)</span>
                              </span>
                            ) : (
                              <span className={styles["muted-text"]}>
                                In Progress
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </BaseModal>
  );
};

export default SkillQueueModal;
