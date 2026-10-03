// React
import ReactDOM from "react-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { loadMenu } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AuthLeftMenu from "@/Menu/AuthLeftMenu";
import type { MenuLinkItem } from "@/Menu/BaseMenu";

export const AuthLeftMenuAsync = () => {
  const { t } = useTranslation();
  const menuRoot =
    typeof document !== "undefined" ? document.getElementById("nav-left") : null;

  const { data: menuData, isLoading: isMenuLoading, isError: menuError } = useQuery({
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

  if (links.length === 0 && isMenuLoading) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <AuthLeftMenu
      error={Boolean(menuError)}
      isLoading={isMenuLoading}
      data={links}
    />,
    menuRoot,
  );
};

export default AuthLeftMenuAsync;
