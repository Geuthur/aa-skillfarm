// React
import React, { useState } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { Coins, AlertCircle, RefreshCw, Calculator, RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";

// Utils
import { renderTooltip } from "@/Utils";

// Styles
import styles from "./ProfitCalculator.module.css";

import { fetchCalculatorData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

export const ProfitCalculator: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: queryKeys.Calculator,
    queryFn: fetchCalculatorData,
  });

  // Inputs
  const [injectorAmount, setInjectorAmount] = useState<string>("3.5");
  const [extractorAmount, setExtractorAmount] = useState<string>("3.5");
  const [duration, setDuration] = useState<number>(1);
  const [useCustomPlex, setUseCustomPlex] = useState<boolean>(false);
  const [customPlexAmount, setCustomPlexAmount] = useState<string>("500");

  // Editable prices (overrides)
  const [customInjectorPrice, setCustomInjectorPrice] = useState<string | null>(null);
  const [customExtractorPrice, setCustomExtractorPrice] = useState<string | null>(null);
  const [customPlexPrice, setCustomPlexPrice] = useState<string | null>(null);

  // Market prices are the default until the user edits a field
  const injectorPriceInput = customInjectorPrice ?? (data?.injector ? Math.round(data.injector.sell).toString() : "");
  const extractorPriceInput = customExtractorPrice ?? (data?.extractor ? Math.round(data.extractor.sell).toString() : "");
  const plexPriceInput = customPlexPrice ?? (data?.plex ? Math.round(data.plex.sell).toString() : "");

  const handleResetPrices = () => {
    setCustomInjectorPrice(null);
    setCustomExtractorPrice(null);
    setCustomPlexPrice(null);
  };

  const handleSyncExtractors = () => {
    setExtractorAmount(injectorAmount);
  };

  const formatISK = (val: number) => {
    return `${Math.round(val).toLocaleString()} ISK`;
  };

  const getProfitClass = (val: number) => (val >= 0 ? styles["profit-positive"] : styles["profit-negative"]);

  // Calculation values
  const injAmt = parseFloat(injectorAmount) || 0;
  const extAmt = parseFloat(extractorAmount) || 0;

  const injPrice =
    parseFloat(injectorPriceInput) || (data?.injector ? data.injector.sell : 0);
  const extPrice =
    parseFloat(extractorPriceInput) || (data?.extractor ? data.extractor.sell : 0);
  const plxPrice =
    parseFloat(plexPriceInput) || (data?.plex ? data.plex.sell : 0);

  let plexMultiplier = 500;
  if (useCustomPlex) {
    plexMultiplier = parseFloat(customPlexAmount) || 0;
  } else {
    if (duration === 1) plexMultiplier = 500;
    else if (duration === 12) plexMultiplier = 300;
    else if (duration === 24) plexMultiplier = 275;
  }

  const grossRevenue = injAmt * injPrice;
  const extractorCost = extAmt * extPrice;
  const totalPlexCost = plxPrice * plexMultiplier;
  const netProfit = grossRevenue - extractorCost - totalPlexCost;
  const hasInputs = injAmt > 0 || extAmt > 0;

  if (isLoading) {
    return (
      <div className={`aa-panel ${styles["state-panel"]}`}>
        <div className="spinner-border text-info mb-2" role="status" />
        <div>{t("Fetching live market data...")}</div>
      </div>
    );
  }

  if (error || data?.error) {
    return (
      <div className={`aa-panel ${styles["error-panel"]}`}>
        <AlertCircle size={28} className={styles["error-icon"]} />
        <h4 className={styles["error-title"]}>{t("Market Data Unavailable")}</h4>
        <p className={styles["error-text"]}>
          {data?.error_message || t("Could not retrieve price aggregates. Please ensure price sync tasks have run.")}
        </p>
        <button
          type="button"
          className="sf-btn sf-btn-secondary"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw size={14} className={isFetching ? "spin" : ""} />
          <span>{t("Try Again")}</span>
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div
        className={styles["header"]}
      >
        <div>
          <h3 className={styles["title"]}>
            <Coins size={24} className={styles["title-icon"]} />
            <span>{t("Skillfarm Calculator")}</span>
          </h3>
          <p className={styles["subtitle"]}>
            {t("Calculate extraction revenue, PLEX subscription costs, and net farm profits in real-time.")}
          </p>
        </div>
        <div className={styles["actions"]}>
          {renderTooltip(
            t("Reset prices to current market rates"),
            <button
              type="button"
              className="sf-btn sf-btn-secondary"
              onClick={handleResetPrices}
            >
              <RotateCcw size={14} />
              <span>{t("Reset Prices")}</span>
            </button>
          )}
          <button
            type="button"
            className="sf-btn sf-btn-secondary"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw size={14} className={isFetching ? "spin" : ""} />
            <span>{t("Refresh Market")}</span>
          </button>
        </div>
      </div>

      {/* Editable Market Prices Cards */}
      <div
        className={styles["price-panel"]}
      >
        <div className="aa-panel">
          <div className={styles["price-row"]}>
            <span className={styles["price-label"]}>
              {t("Skill Injector Price")}
            </span>
            <small className={styles["price-hint"]}>{t("Jita Sell: {{price}}", { price: data?.injector ? formatISK(data.injector.sell) : "-" })}</small>
          </div>
          <div className="input-group">
            <input
              type="number"
              className="form-control"
              value={injectorPriceInput}
              onChange={(e) => setCustomInjectorPrice(e.target.value)}
              placeholder={t("Injector ISK")}
            />
            <span className="input-group-text bg-dark text-muted">ISK</span>
          </div>
        </div>

        <div className="aa-panel">
          <div className={styles["price-row"]}>
            <span className={styles["price-label"]}>
              {t("Skill Extractor Price")}
            </span>
            <small className={styles["price-hint"]}>{t("Jita Sell: {{price}}", { price: data?.extractor ? formatISK(data.extractor.sell) : "-" })}</small>
          </div>
          <div className="input-group">
            <input
              type="number"
              className="form-control"
              value={extractorPriceInput}
              onChange={(e) => setCustomExtractorPrice(e.target.value)}
              placeholder={t("Extractor ISK")}
            />
            <span className="input-group-text bg-dark text-muted">ISK</span>
          </div>
        </div>

        <div className="aa-panel">
          <div className={styles["price-row"]}>
            <span className={styles["price-label"]}>
              {t("PLEX Unit Price")}
            </span>
            <small className={styles["price-hint"]}>{t("Jita Sell: {{price}}", { price: data?.plex ? formatISK(data.plex.sell) : "-" })}</small>
          </div>
          <div className="input-group">
            <input
              type="number"
              className="form-control"
              value={plexPriceInput}
              onChange={(e) => setCustomPlexPrice(e.target.value)}
              placeholder={t("PLEX ISK")}
            />
            <span className="input-group-text bg-dark text-muted">ISK</span>
          </div>
        </div>
      </div>

      {/* Interactive Calculation Form */}
      <div className={`aa-panel mb-4 ${styles["settings-panel"]}`}>
        <h4 className={styles["section-title"]}>
          <Calculator size={18} className={styles["section-icon"]} />
          <span>{t("Calculation Parameters")}</span>
        </h4>

        <div className="row g-3">
          <div className="col-md-6">
            <label className="form-label text-secondary small fw-bold">{t("Skill Injector Amount")}</label>
            <input
              type="number"
              step="0.1"
              min="0"
              className="form-control"
              value={injectorAmount}
              onChange={(e) => setInjectorAmount(e.target.value)}
              placeholder="e.g. 3.5"
            />
            <small className="text-muted">{t("Standard rate is 3.5 injectors / month.")}</small>
          </div>

          <div className="col-md-6">
            <div className="d-flex justify-content-between align-items-center">
              <label className="form-label text-secondary small fw-bold mb-0">{t("Skill Extractor Amount")}</label>
              <button
                type="button"
                className={`btn btn-link btn-sm p-0 text-decoration-none ${styles["link-small"]}`}
                onClick={handleSyncExtractors}
              >
                {t("Match Injectors ({{amount}})", { amount: injectorAmount || 0 })}
              </button>
            </div>
            <input
              type="number"
              step="0.1"
              min="0"
              className="form-control mt-1"
              value={extractorAmount}
              onChange={(e) => setExtractorAmount(e.target.value)}
              placeholder="e.g. 3.5"
            />
            <small className="text-muted">{t("Extractors consumed to produce the injectors.")}</small>
          </div>

          <div className="col-md-6">
            <label className="form-label text-secondary small fw-bold">{t("Subscription Plan / Duration")}</label>
            <select
              className="form-select"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              disabled={useCustomPlex}
            >
              <option value={1}>{t("Monthly Plan (500 PLEX / mo)")}</option>
              <option value={12}>{t("12 Months Plan (300 PLEX / mo)")}</option>
              <option value={24}>{t("24 Months Plan (275 PLEX / mo)")}</option>
            </select>
          </div>

          <div className="col-md-6">
            <div className="form-check mt-3 mb-1">
              <input
                className="form-check-input"
                type="checkbox"
                id="custom-plex-check"
                checked={useCustomPlex}
                onChange={(e) => setUseCustomPlex(e.target.checked)}
              />
              <label className="form-check-label text-secondary small fw-bold" htmlFor="custom-plex-check">
                {t("Use custom PLEX amount")}
              </label>
            </div>
            {useCustomPlex && (
              <input
                type="number"
                min="0"
                className="form-control"
                value={customPlexAmount}
                onChange={(e) => setCustomPlexAmount(e.target.value)}
                placeholder={t("PLEX amount")}
              />
            )}
          </div>
        </div>

        {/* Dynamic Calculation Result */}
        <div className="mt-4 pt-3 border-top border-secondary">
          {!hasInputs ? (
            <div className="alert alert-warning mb-0 small">
              {t("Please enter an amount for Skill Injectors or Extractors to calculate profit.")}
            </div>
          ) : (
            <div>
              <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                <span className={`text-secondary fw-bold ${styles["summary-label"]}`}>
                  {t("Calculated Net Result:")}
                </span>
                <span className={`${styles["net-profit"]} ${getProfitClass(netProfit)}`}>
                  {formatISK(netProfit)}
                </span>
              </div>

              {/* Financial Breakdown Table */}
              <div className="table-responsive">
                <table className={`table table-dark table-sm table-striped mb-0 ${styles["breakdown-table"]}`}>
                  <tbody>
                    <tr>
                      <td className="text-secondary">{t("Gross Injector Revenue ({{amount}} × {{price}})", { amount: injAmt, price: formatISK(injPrice) })}</td>
                      <td className="text-end text-success fw-bold">+{formatISK(grossRevenue)}</td>
                    </tr>
                    <tr>
                      <td className="text-secondary">{t("Extractor Cost ({{amount}} × {{price}})", { amount: extAmt, price: formatISK(extPrice) })}</td>
                      <td className="text-end text-danger fw-bold">-{formatISK(extractorCost)}</td>
                    </tr>
                    <tr>
                      <td className="text-secondary">{t("PLEX Subscription Cost ({{amount}} PLEX × {{price}})", { amount: plexMultiplier, price: formatISK(plxPrice) })}</td>
                      <td className="text-end text-danger fw-bold">-{formatISK(totalPlexCost)}</td>
                    </tr>
                    <tr className="table-active">
                      <td className="fw-bold">{t("Total Net Profit / Loss")}</td>
                      <td className={`text-end fw-bold ${getProfitClass(netProfit)}`}>
                        {formatISK(netProfit)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Benchmark Monthly Projections (Standard 3.5 Injectors) */}
      <h4 className={styles["results-title"]}>
        {t("Monthly Reference Projections (3.5 Injectors / mo)")}
      </h4>

      <div
        className={styles["results-grid"]}
      >
        <div className={`aa-panel ${styles["result-card-blue"]}`}>
          <div className="d-flex justify-content-between align-items-center">
            <span className={styles["result-name"]}>{t("1-Month Plan")}</span>
            <span className={styles["result-duration"]}>{t("500 PLEX/mo")}</span>
          </div>
          <div className={`${styles["result-value"]} ${getProfitClass(data?.month_calc ?? 0)}`}>
            {data ? formatISK(data.month_calc) : "-"}
          </div>
          <p className={styles["result-note"]}>
            {t("Standard monthly subscription rate with PLEX.")}
          </p>
        </div>

        <div className={`aa-panel ${styles["result-card-amber"]}`}>
          <div className="d-flex justify-content-between align-items-center">
            <span className={styles["result-name"]}>{t("12-Month Plan")}</span>
            <span className={styles["result-duration"]}>{t("300 PLEX/mo")}</span>
          </div>
          <div className={`${styles["result-value"]} ${getProfitClass(data?.month12_calc ?? 0)}`}>
            {data ? formatISK(data.month12_calc) : "-"}
          </div>
          <p className={styles["result-note"]}>
            {t("Annual package rate discount (~40% PLEX savings).")}
          </p>
        </div>

        <div className={`aa-panel ${styles["result-card-emerald"]}`}>
          <div className="d-flex justify-content-between align-items-center">
            <span className={styles["result-name"]}>{t("24-Month Plan")}</span>
            <span className={styles["result-duration"]}>{t("275 PLEX/mo")}</span>
          </div>
          <div className={`${styles["result-value"]} ${getProfitClass(data?.month24_calc ?? 0)}`}>
            {data ? formatISK(data.month24_calc) : "-"}
          </div>
          <p className={styles["result-note"]}>
            {t("Maximum 2-year package rate discount.")}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProfitCalculator;
