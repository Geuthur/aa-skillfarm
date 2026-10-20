// React
import { Link, useLocation } from "react-router-dom";

// Third Party
import { ShieldAlert } from "lucide-react";
import { Nav } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { components } from "@/Api/OpenApi";

export type MenuLinkItem = components["schemas"]["MenuLink"];

export interface MenuCategory {
    name: string;
    link?: string;
    links?: MenuLinkItem[];
}

export interface MenuProps {
    isLoading: boolean;
    data: Array<MenuCategory | MenuLinkItem>;
    error: boolean;
}

export interface ToPath {
    toPath: (link: string) => string;
}

export const SuperuserMenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.endsWith(link.link ?? "");

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: toPath(link.link ?? ""), search: path.search }}
                id={link.name}
                key={link.name}
                active={hit}
                className="aa-nav-danger d-flex align-items-center gap-1"
                data-testid="superuser-nav-link"
            >
                <ShieldAlert size={15} className="text-danger flex-shrink-0" />
                <span>{t(link.name)}</span>
            </Nav.Link>
        </Nav.Item>
    );
};

export const MenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.endsWith(link.link ?? "");
    const isExternal = Boolean(
        link.is_external ||
        link.link?.startsWith("http://") ||
        link.link?.startsWith("https://")
    );

    if (isExternal) {
        return (
            <Nav.Item as="li">
                <Nav.Link
                    href={link.link ?? "#"}
                    id={link.name}
                    key={link.name}
                >
                    {t(link.name)}
                </Nav.Link>
            </Nav.Item>
        );
    }

    const isSuperuserLink = Boolean(
        link.link?.replace(/^\/+|\/+$/g, "") === "superuser" ||
        link.name.toLowerCase() === "superuser"
    );

    if (isSuperuserLink) {
        return <SuperuserMenuItem link={link} toPath={toPath} />;
    }

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: toPath(link.link ?? ""), search: path.search }}
                id={link.name}
                key={link.name}
                active={hit}
                className={link.has_errors ? "aa-order-nav-pulse" : ""}
            >
                {link.has_errors && (
                    <span className="aa-pending-dot-container me-1" aria-hidden="true">
                        <span className="aa-danger-dot-ping" />
                        <span className="aa-danger-dot-core" />
                    </span>
                )}
                {t(link.name)}
                {link.badge ? (
                    <span className="badge bg-danger ms-1">{link.badge}</span>
                ) : null}
            </Nav.Link>
        </Nav.Item>
    );
};
