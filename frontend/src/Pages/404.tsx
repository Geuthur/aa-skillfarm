// Third Party
import { useTranslation } from "react-i18next";

// AA Skillfarm
import { ErrorLoader } from "@/Components/Loader";

export function ErrorPage() {
  const { t } = useTranslation();
  return (
    <main className="aa-panel-lg">
      <ErrorLoader
        title={t("Error 404")}
        message={t("The page you are looking for does not exist.")}
      />
    </main>
  );
}

export default ErrorPage;
