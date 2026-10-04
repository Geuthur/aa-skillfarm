// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TrainingProgressBar } from "./TrainingProgressBar";

describe("TrainingProgressBar", () => {
  it("should render inactive badge with warning class when isTraining is false and not acknowledged", () => {
    // Test Data
    const isTraining = false;

    // Test Action
    const { container } = render(<TrainingProgressBar isTraining={isTraining} queuePausedAcknowledged={false} />);

    // Expected Result
    expect(screen.getByText(/Training Inactive/i)).toBeInTheDocument();
    expect(container.querySelector(".sf-badge-idle")).toBeInTheDocument();
    expect(container.querySelector(".sf-badge-idle-acknowledged")).not.toBeInTheDocument();
  });

  it("should render acknowledged badge class and label when queuePausedAcknowledged is true", () => {
    // Test Data
    const isTraining = false;

    // Test Action
    const { container } = render(<TrainingProgressBar isTraining={isTraining} queuePausedAcknowledged={true} />);

    // Expected Result
    expect(screen.getByText(/Training Inactive/i)).toBeInTheDocument();
    expect(screen.getByText(/\(Acknowledged\)/i)).toBeInTheDocument();
    expect(container.querySelector(".sf-badge-idle-acknowledged")).toBeInTheDocument();
    expect(container.querySelector(".sf-badge-idle")).not.toBeInTheDocument();
  });

  it("should render skill details and progress track when isTraining is true", () => {
    // Test Data
    const isTraining = true;
    const currentSkill = "Cybernetics V";
    const finishDate = "2026-10-15 14:00";

    // Test Action
    render(
      <TrainingProgressBar
        isTraining={isTraining}
        currentSkill={currentSkill}
        trainingFinishDate={finishDate}
      />
    );

    // Expected Result
    expect(screen.getByText("Cybernetics V")).toBeInTheDocument();
    expect(screen.getByText(/Skill Finishes: 10-15 14:00/i)).toBeInTheDocument();
    expect(screen.getByText(/Active/i)).toBeInTheDocument();
  });

  it("should display dynamically calculated progress percentage", () => {
    // Test Data
    const isTraining = true;
    const currentSkill = "Advanced Spaceship Command V";
    const progressPercent = 75.5;

    // Test Action
    render(
      <TrainingProgressBar
        isTraining={isTraining}
        currentSkill={currentSkill}
        progressPercent={progressPercent}
      />
    );

    // Expected Result
    expect(screen.getByText(/Active \(75.5%\)/i)).toBeInTheDocument();
  });
});
