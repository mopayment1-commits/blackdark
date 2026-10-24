/**
 * Public-layer decision labels (mirrors supplemental_public_compliance.map_public_decision_action).
 */
(function (global) {
    function mapPublicDecisionAction(raw) {
        const token = String(raw ?? "").trim().toUpperCase();
        if (token === "ACT" || token === "BUY" || token === "LONG" || token === "BULLISH" || token === "BULLISH_ANALYTICS") {
            return "CONDITIONS MET";
        }
        if (
            token === "SELL" ||
            token === "SHORT" ||
            token === "EXIT" ||
            token === "CAUTION" ||
            token === "AVOID" ||
            token === "DO_NOT_TOUCH" ||
            token === "BEARISH" ||
            token === "BEARISH_ANALYTICS"
        ) {
            return "ABSTAIN";
        }
        if (token === "WAIT" || token === "HOLD" || token === "NEUTRAL" || token === "NEUTRAL_OBSERVE" || token === "ABSTAIN") {
            return "WAIT";
        }
        if (token.includes("CONDITION")) {
            return "CONDITIONS MET";
        }
        if (token === "ELEVATED_RISK") {
            return "ABSTAIN";
        }
        return "WAIT";
    }

    const ACTION_I18N_KEYS = {
        WAIT: "action.WAIT",
        ACT: "action.ACT",
        "CONDITIONS MET": "action.CONDITIONS_MET",
        ABSTAIN: "action.ABSTAIN",
        CAUTION: "action.CAUTION",
    };

    function localizePublicDecisionAction(rawOrMapped) {
        const mapped = ACTION_I18N_KEYS[rawOrMapped]
            ? rawOrMapped
            : mapPublicDecisionAction(rawOrMapped);
        const key = ACTION_I18N_KEYS[mapped];
        const i18n = global.BD_I18N;
        if (key && i18n && typeof i18n.t === "function") {
            const label = i18n.t(key);
            if (label) return label;
        }
        return mapped;
    }

    function mapAndLocalizePublicDecisionAction(raw) {
        const mapped = mapPublicDecisionAction(raw);
        return localizePublicDecisionAction(mapped);
    }

    global.BDPublicDecision = {
        mapPublicDecisionAction,
        localizePublicDecisionAction,
        mapAndLocalizePublicDecisionAction,
    };
})(typeof window !== "undefined" ? window : globalThis);
