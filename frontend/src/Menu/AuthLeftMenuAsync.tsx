// React
import ReactDOM from "react-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { loadMenu, loadUserData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AuthLeftMenu from "@/Menu/AuthLeftMenu";
import type { MenuLinkItem } from "@/Menu/BaseMenu";

export const AuthLeftMenuAsync = () => {
  const { t } = useTranslation();
  const menuRoot =
    typeof document !== "undefined" ? document.getElementById("nav-left") : null;

  const {
    isLoading: isUserLoading,
    error: userError,
    data: userData,
  } = useQuery({
    queryKey: queryKeys.User,
    queryFn: () => loadUserData(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: menuData, isLoading: isMenuLoading } = useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  if (!menuRoot) {
    return <></>;
  }

  let links: MenuLinkItem[];

  if (menuData?.left_links?.length) {
    links = [...menuData.left_links];
  } else {
    links = [
      { name: t("Characters"), link: "/", is_external: false },
      { name: t("Calculator"), link: "/calculator/", is_external: false },
    ];
  }

  if (userData?.user?.is_admin && !links.some((l) => l.link?.includes("admin"))) {
    links.push({
      name: t("Administration"),
      link: "/admin/",
      is_external: false,
    });
  }

  if (links.length === 0 && isUserLoading) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <AuthLeftMenu
      error={Boolean(userError)}
      isLoading={isUserLoading || isMenuLoading}
      data={links}
    />,
    menuRoot,
  );
};

export default AuthLeftMenuAsync;
