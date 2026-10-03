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

    global.BDPublicDecision = { mapPublicDecisionAction };
})(typeof window !== "undefined" ? window : globalThis);
