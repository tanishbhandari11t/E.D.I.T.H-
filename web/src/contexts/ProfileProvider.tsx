import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useSearchParams } from "react-router";
import { api, setManagementProfile } from "@/lib/api";
import { ProfileContext } from "@/contexts/profile-context";

/**
 * Machine-level management-profile scope.
 *
 * One switcher (rendered in the sidebar) decides which profile every
 * management page reads/writes. React STATE is the source of truth; the
 * URL (`?profile=<name>`) is a synchronized projection of it so deep links
 * land scoped and refresh survives. The selection is mirrored into the api
 * module so `fetchJSON` transparently appends it to the profile-scoped
 * endpoint families. "" = the dashboard's own profile.
 *
 * When ``/api/auth/me`` returns a non-empty ``profile``, that value is
 * locked for the session (EDITH multi-user): the switcher is hidden and
 * ``setProfile`` is a no-op so users cannot open another EDITH's chats.
 */
export function ProfileProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const { pathname } = useLocation();
  const [profiles, setProfiles] = useState<string[]>([]);
  const [currentProfile, setCurrentProfile] = useState("default");
  const [profileLocked, setProfileLocked] = useState(false);

  // Initial value comes from the URL (deep link / refresh / unified-launch
  // preselect); afterwards state leads and the URL follows.
  const [profile, setProfileState] = useState(
    () => searchParams.get("profile") ?? "",
  );

  // Mirror into the api module synchronously on every render where it
  // changed, so fetches fired by child effects in the same commit see it.
  setManagementProfile(profile);

  // A profile param arriving via in-app navigation (e.g. the Profiles
  // page's "Manage skills & tools" linking to /skills?profile=X) must win
  // over current state — it's an explicit scope request.
  // When locked, ignore foreign URL profiles.
  const urlProfile = searchParams.get("profile");
  useEffect(() => {
    if (profileLocked) return;
    if (urlProfile !== null && urlProfile !== profile) {
      setManagementProfile(urlProfile);
      setProfileState(urlProfile);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlProfile, profileLocked]);

  // Re-assert ?profile= after navigations that dropped it (bare nav links).
  // Runs on every pathname/profile change; no-ops when already in sync.
  useEffect(() => {
    const inUrl = searchParams.get("profile") ?? "";
    if ((profile || "") === inUrl) return;
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (profile) next.set("profile", profile);
        else next.delete("profile");
        return next;
      },
      { replace: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, profile]);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      api.getProfiles().catch(() => null),
      api.getActiveProfile().catch(() => null),
      api.getAuthMe().catch(() => null),
    ]).then(([profilesRes, info, me]) => {
      if (cancelled) return;

      if (profilesRes) {
        setProfiles(profilesRes.profiles.map((p) => p.name));
      }

      const bound = (me?.profile || "").trim();
      if (bound) {
        setProfileLocked(true);
        setManagementProfile(bound);
        setProfileState(bound);
        setCurrentProfile(bound);
        return;
      }

      if (info) {
        const current = info.current || "default";
        const active = info.active || "default";
        setCurrentProfile(current);
        const urlP = searchParams.get("profile");
        if (urlP === null && active !== current) {
          setManagementProfile(active);
          setProfileState(active);
        }
      }
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setProfile = useCallback(
    (name: string) => {
      if (profileLocked) return;
      setManagementProfile(name);
      setProfileState(name);
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (name) next.set("profile", name);
          else next.delete("profile");
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams, profileLocked],
  );

  const value = useMemo(
    () => ({ profile, currentProfile, profiles, setProfile, profileLocked }),
    [profile, currentProfile, profiles, setProfile, profileLocked],
  );

  return (
    <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
  );
}
