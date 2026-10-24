// React
import { useState } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { Button, Table } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA Skillfarm
import { loadAdministrationCorporations, loadAdministrationUnregistered } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { AdministrationCorporationSchema } from "@/Api/schema";
import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";
import { UnregisteredModal } from "@/Components/Base/OwnerSettings/UnregisteredModal";

/** Corporations (own corporation or all) with their registered and unregistered characters. */
export const AdministrationCorporationsTable = () => {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<AdministrationCorporationSchema | null>(null);

  const {
    data: corporations,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.AdministrationCorporations,
    queryFn: loadAdministrationCorporations,
  });

  const {
    data: unregistered,
    isLoading: isLoadingUnregistered,
    isError: isErrorUnregistered,
  } = useQuery({
    queryKey: queryKeys.AdministrationUnregistered(selected?.corporation_id ?? null),
    queryFn: () => loadAdministrationUnregistered(selected!.corporation_id),
    enabled: Boolean(selected),
  });

  if (isLoading) return <FetchingLoader />;
  if (isError) return <ErrorLoader message={t("Failed to load corporations.")} />;

  return (
    <>
      <Table responsive hover size="sm" className="align-middle mb-0" data-testid="corporations-table">
        <thead>
          <tr>
            <th aria-label={t("Logo")} style={{ width: 48 }} />
            <th>{t("Corporation")}</th>
            <th className="text-end">{t("Registered")}</th>
            <th className="text-end">{t("Unregistered")}</th>
          </tr>
        </thead>
        <tbody>
          {(corporations ?? []).map((corp) => (
            <tr key={corp.corporation_id}>
              <td>
                <img src={corp.logo_url} alt="" width={32} height={32} className="rounded" />
              </td>
              <td>
                <span className="fw-semibold">{corp.corporation_name}</span>{" "}
                <span className="text-muted small">[{corp.corporation_ticker}]</span>
              </td>
              <td className="text-end">{corp.registered_count}</td>
              <td className="text-end">
                <Button
                  variant="link"
                  size="sm"
                  className="py-0 px-2 text-decoration-none"
                  onClick={() => setSelected(corp)}
                  data-testid={`unregistered-btn-${corp.corporation_id}`}
                >
                  {corp.unregistered_count} {t("Unregistered")}
                </Button>
              </td>
            </tr>
          ))}
          {(corporations ?? []).length === 0 && (
            <tr>
              <td colSpan={4} className="text-center text-muted py-3">
                {t("No corporations found.")}
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      <UnregisteredModal
        show={Boolean(selected)}
        onHide={() => setSelected(null)}
        title={t("Unregistered members of {{name}}", { name: selected?.corporation_name ?? "" })}
        description={t("Characters of this corporation that are not registered in Skillfarm.")}
        items={unregistered?.items ?? []}
        isLoading={isLoadingUnregistered}
        isError={isErrorUnregistered}
        errorMessage={t("Failed to load unregistered entries.")}
        emptyMessage={t("Everything is registered.")}
      />
    </>
  );
};

export default AdministrationCorporationsTable;
