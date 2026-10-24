// React
import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { Eye, Search, Shield, User } from "lucide-react";
import { Badge, Card, Col, Form, InputGroup, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { fetchOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { ProjectName } from "@/constants";

export const OverviewPage: React.FC = () => {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.Overview,
    queryFn: fetchOverview,
  });

  const filteredUsers = useMemo(() => {
    if (!data?.users) return [];
    if (!search.trim()) return data.users;
    const q = search.trim().toLowerCase();
    return data.users.filter(
      (u) =>
        u.main_character_name.toLowerCase().includes(q) ||
        u.username.toLowerCase().includes(q) ||
        u.corporation_name.toLowerCase().includes(q) ||
        u.corporation_ticker.toLowerCase().includes(q),
    );
  }, [data, search]);

  return (
    <Card className="border-0 bg-transparent">
      <BaseSectionHeader name={t("Skillfarm Overview")}>
        <div className="d-flex align-items-center gap-2">
          <Badge bg="secondary" className="px-3 py-2">
            {filteredUsers.length} {t("Users")}
          </Badge>
        </div>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
          <InputGroup style={{ maxWidth: 360 }}>
            <InputGroup.Text className="bg-dark border-secondary text-secondary">
              <Search size={16} />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder={t("Search users & corporations…")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-dark text-light border-secondary"
            />
          </InputGroup>
        </div>

        {isLoading && (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <div className="mt-2 text-muted">{t("Loading overview…")}</div>
          </div>
        )}

        {isError && (
          <div className="text-center py-5">
            <Shield size={48} className="mb-3 text-warning opacity-75" />
            <h3 className="h4 text-light">{t("Permission Denied")}</h3>
            <p className="text-muted small">
              {t("You do not have access to the overview of other users.")}
            </p>
          </div>
        )}

        {!isLoading && !isError && filteredUsers.length === 0 && (
          <div className="text-center py-5 text-muted">
            <Shield size={48} className="mb-3 opacity-50" />
            <h5>{t("No users found")}</h5>
            <p className="small">
              {t("There are no Skillfarm characters visible to you.")}
            </p>
          </div>
        )}

        <Row className="g-3">
          {filteredUsers.map((user) => (
            <Col key={user.user_id} xs={12} md={6} lg={4}>
              <Card className="h-100 aa-card border-secondary shadow-sm">
                <Card.Body className="d-flex flex-column justify-content-between p-3">
                  <div>
                    <div className="d-flex align-items-center gap-3 mb-3">
                      {user.portrait_url ? (
                        <img
                          src={user.portrait_url}
                          alt={user.main_character_name}
                          width={48}
                          height={48}
                          className="rounded-circle border border-secondary"
                        />
                      ) : (
                        <div
                          className="rounded-circle bg-secondary d-flex align-items-center justify-content-center text-white"
                          style={{ width: 48, height: 48 }}
                        >
                          <User size={24} />
                        </div>
                      )}
                      <div className="overflow-hidden">
                        <h5 className="mb-0 text-truncate text-light">
                          {user.main_character_name}
                        </h5>
                        {user.corporation_name && (
                          <div className="text-muted small text-truncate mt-1">
                            {user.corporation_name}{" "}
                            {user.corporation_ticker ? `[${user.corporation_ticker}]` : ""}
                          </div>
                        )}
                        <div className="d-flex align-items-center gap-2 mt-1">
                          <Badge bg="info" className="text-dark">
                            {user.character_count} {t("Characters")}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div className="aa-panel d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3 p-2 rounded border border-secondary small">
                      <div className="d-flex align-items-center gap-1">
                        <span className="text-muted">{t("Training")}:</span>
                        <Badge bg={user.training_count > 0 ? "success" : "secondary"}>
                          {user.training_count}
                        </Badge>
                      </div>
                      <div className="d-flex align-items-center gap-1">
                        <span className="text-muted">{t("Paused")}:</span>
                        <Badge
                          bg={user.paused_count > 0 ? "warning" : "secondary"}
                          className={user.paused_count > 0 ? "text-dark" : ""}
                        >
                          {user.paused_count}
                        </Badge>
                      </div>
                      <div className="d-flex align-items-center gap-1">
                        <span className="text-muted">{t("Ready")}:</span>
                        <Badge
                          bg={user.pending_extractions_count > 0 ? "primary" : "secondary"}
                        >
                          {user.pending_extractions_count}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="d-flex flex-wrap gap-2 pt-2 border-top border-secondary">
                    <Link
                      to={`/${ProjectName}/overview/${user.user_id}/`}
                      className="sf-btn sf-btn-sm sf-btn-primary flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <Eye size={14} />
                      {t("Characters")}
                    </Link>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </Card>
  );
};

export default OverviewPage;
