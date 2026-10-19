// Third Party
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA Skillfarm
import { ErrorLoader } from "@/Components/Base/Loader";

export function ErrorPage() {
  const { t } = useTranslation();
  return (
    <Card className="bg-secondary text-light border-0 shadow-sm">
      <Card.Body className="p-4 text-center">
        <ErrorLoader
          title={t("Error 404")}
          message={t("The page you are looking for does not exist.")}
        />
      </Card.Body>
    </Card>
  );
}

export default ErrorPage;
