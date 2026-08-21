import { createContext } from "react";

export interface ProfileContextValue {
  /** Profile every management surface reads/writes ("" = the dashboard
   *  process's own profile). */
  profile: string;
  /** The profile the dashboard process itself runs under. */
  currentProfile: string;
  /** Known profile names (includes "default"). */
  profiles: string[];
  setProfile: (name: string) => void;
  /** When true, auth bound the user to ``profile`` — switcher must hide. */
  profileLocked: boolean;
}

export const ProfileContext = createContext<ProfileContextValue>({
  profile: "",
  currentProfile: "default",
  profiles: [],
  setProfile: () => {},
  profileLocked: false,
});
