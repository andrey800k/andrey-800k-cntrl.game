"""
CNTRL.GAMES — сканер игровых процессов (Windows).

    from process_monitor import get_running_games
    games = get_running_games()                      # только игры
    games = get_running_games(include_launchers=True)  # + Steam, Epic, Battle.net...

Каждый элемент: {"exe", "title", "pid", "category", "count"}
  category — "game" | "launcher";  count — сколько процессов с таким exe запущено.
Тест:  python process_monitor.py
"""
import sys
import time

import psutil

# exe (нижний регистр) -> (название, категория)
GAME_EXECUTABLES: dict[str, tuple[str, str]] = {
    # --- Игры ---
    "robloxplayerbeta.exe":  ("Roblox", "game"),
    "robloxstudiobeta.exe":  ("Roblox Studio", "game"),
    "cs2.exe":               ("Counter-Strike 2", "game"),
    "csgo.exe":              ("Counter-Strike: GO", "game"),
    "dota2.exe":             ("Dota 2", "game"),
    "minecraft.windows.exe": ("Minecraft (Bedrock)", "game"),
    "javaw.exe":             ("Minecraft (Java)", "game"),   # см. AMBIGUOUS_HINTS
    "gta5.exe":              ("Grand Theft Auto V", "game"),
    "gta5_enhanced.exe":     ("Grand Theft Auto V", "game"),
    "rdr2.exe":              ("Red Dead Redemption 2", "game"),
    "fortniteclient-win64-shipping.exe": ("Fortnite", "game"),
    "tslgame.exe":           ("PUBG: Battlegrounds", "game"),
    "r5apex.exe":            ("Apex Legends", "game"),
    "r5apex_dx12.exe":       ("Apex Legends", "game"),
    "brawlhalla.exe":        ("Brawlhalla", "game"),
    "rustclient.exe":        ("Rust", "game"),
    "escapefromtarkov.exe":  ("Escape from Tarkov", "game"),
    "worldoftanks.exe":      ("World of Tanks", "game"),
    "wotblitz.exe":          ("WoT Blitz", "game"),
    "worldofwarships64.exe": ("World of Warships", "game"),
    "league of legends.exe": ("League of Legends", "game"),
    "valorant-win64-shipping.exe": ("VALORANT", "game"),
    "genshinimpact.exe":     ("Genshin Impact", "game"),
    "yuanshen.exe":          ("Genshin Impact", "game"),
    "starrail.exe":          ("Honkai: Star Rail", "game"),
    "bh3.exe":               ("Honkai Impact 3rd", "game"),
    "zenlesszonezero.exe":   ("Zenless Zone Zero", "game"),
    "rocketleague.exe":      ("Rocket League", "game"),
    "overwatch.exe":         ("Overwatch 2", "game"),
    "cod.exe":               ("Call of Duty / Warzone", "game"),
    "rainbowsix.exe":        ("Rainbow Six Siege", "game"),
    "rainbowsix_vulkan.exe": ("Rainbow Six Siege", "game"),
    "destiny2.exe":          ("Destiny 2", "game"),
    "eldenring.exe":         ("Elden Ring", "game"),
    "cyberpunk2077.exe":     ("Cyberpunk 2077", "game"),
    "witcher3.exe":          ("The Witcher 3", "game"),
    "terraria.exe":          ("Terraria", "game"),
    "stardew valley.exe":    ("Stardew Valley", "game"),
    "among us.exe":          ("Among Us", "game"),
    "fallguys_client_game.exe": ("Fall Guys", "game"),
    "warframe.x64.exe":      ("Warframe", "game"),
    "pathofexile_x64.exe":   ("Path of Exile", "game"),
    "diablo iv.exe":         ("Diablo IV", "game"),
    "wow.exe":               ("World of Warcraft", "game"),
    "hearthstone.exe":       ("Hearthstone", "game"),
    "fc25.exe":              ("EA Sports FC 25", "game"),
    "fc24.exe":              ("EA Sports FC 24", "game"),
    "deadbydaylight-win64-shipping.exe": ("Dead by Daylight", "game"),
    "lethal company.exe":    ("Lethal Company", "game"),
    "palworld-win64-shipping.exe": ("Palworld", "game"),
    "helldivers2.exe":       ("Helldivers 2", "game"),
    "bg3.exe":               ("Baldur's Gate 3", "game"),
    "bg3_dx11.exe":          ("Baldur's Gate 3", "game"),
    "hogwartslegacy.exe":    ("Hogwarts Legacy", "game"),
    "tf_win64.exe":          ("Team Fortress 2", "game"),
    "left4dead2.exe":        ("Left 4 Dead 2", "game"),
    "gmod.exe":              ("Garry's Mod", "game"),
    "osu!.exe":              ("osu!", "game"),
    "marvel-win64-shipping.exe": ("Marvel Rivals", "game"),
    # --- Лаунчеры ---
    "steam.exe":             ("Steam", "launcher"),
    "epicgameslauncher.exe": ("Epic Games Launcher", "launcher"),
    "battle.net.exe":        ("Battle.net", "launcher"),
    "eadesktop.exe":         ("EA app", "launcher"),
    "origin.exe":            ("Origin", "launcher"),
    "upc.exe":               ("Ubisoft Connect", "launcher"),
    "galaxyclient.exe":      ("GOG Galaxy", "launcher"),
    "riotclientservices.exe": ("Riot Client", "launcher"),
    "leagueclient.exe":      ("League of Legends Client", "launcher"),
    "minecraftlauncher.exe": ("Minecraft Launcher", "launcher"),
    "wgc.exe":               ("Wargaming Game Center", "launcher"),
}

# Универсальные процессы: считаем игрой, только если подстрока есть в командной строке.
# (javaw.exe запускает любое Java-приложение, не только Minecraft.)
AMBIGUOUS_HINTS: dict[str, str] = {"javaw.exe": "minecraft"}


def _is_confirmed(proc: psutil.Process, exe: str) -> bool:
    """Для неоднозначных exe проверяет командную строку. Нет доступа — считаем, что не игра."""
    hint = AMBIGUOUS_HINTS.get(exe)
    if hint is None:
        return True
    try:
        return hint in " ".join(proc.cmdline()).lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def get_running_games(include_launchers: bool = False, dedupe: bool = True) -> list[dict]:
    """
    Быстрый скан процессов (читается только имя; cmdline — лишь для неоднозначных exe).
    dedupe=True  — одна запись на exe (pid первого найденного, count = число процессов);
    dedupe=False — отдельная запись на каждый процесс.
    """
    found: dict[str, dict] = {}
    result: list[dict] = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            entry = GAME_EXECUTABLES.get(name)
            if entry is None:
                continue
            title, category = entry
            if category == "launcher" and not include_launchers:
                continue
            if not _is_confirmed(proc, name):
                continue
            pid = proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue                        # процесс исчез / закрыт для чтения — пропускаем

        if dedupe and name in found:
            found[name]["count"] += 1
            continue
        item = {"exe": name, "title": title, "pid": pid, "category": category, "count": 1}
        result.append(item)
        if dedupe:
            found[name] = item

    return sorted(result, key=lambda x: (x["category"] != "game", x["title"].lower()))


def register_games(extra: dict[str, tuple[str, str]]) -> None:
    """Дополнить словарь (например, играми из Supabase): {"game.exe": ("Название", "game")}."""
    GAME_EXECUTABLES.update({k.lower(): v for k, v in extra.items()})


# ------------------------------------------------------------------ тест
def _print_section(title: str, items: list[dict]) -> None:
    print(f"\n  {title}")
    if not items:
        print("    — ничего не запущено")
        return
    print(f"    {'Название':<28}{'Процесс':<34}{'PID':>8}  {'Шт.':>3}")
    print("    " + "─" * 76)
    for g in items:
        print(f"    {g['title']:<28}{g['exe']:<34}{g['pid']:>8}  {g['count']:>3}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")     # корректная кириллица в консоли Windows
    except AttributeError:
        pass

    t0 = time.perf_counter()
    running = get_running_games(include_launchers=True)
    ms = (time.perf_counter() - t0) * 1000

    print("\n  ╔" + "═" * 56 + "╗")
    print("  ║" + "CNTRL.GAMES · Монитор процессов".center(56) + "║")
    print("  ╚" + "═" * 56 + "╝")
    print(f"  В словаре: {len(GAME_EXECUTABLES)} exe · скан занял {ms:.1f} мс")

    _print_section("🎮 Игры", [g for g in running if g["category"] == "game"])
    _print_section("🚀 Лаунчеры", [g for g in running if g["category"] == "launcher"])
    print()
