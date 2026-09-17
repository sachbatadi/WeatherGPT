def generate_voice_script(alert):
    language = alert.recipient.language.strip().lower()
    hazard = alert.hazard.strip()
    location = alert.location.strip()
    eta = alert.eta_minutes
    actions = alert.approved_actions

    # -------------------------
    # PUNJABI
    # -------------------------
    if language == "punjabi":

        hazard_lower = hazard.lower()

        if "rain" in hazard_lower:
            hazard_text = "ਭਾਰੀ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        elif "flood" in hazard_lower:
            hazard_text = "ਹੜ੍ਹ ਆਉਣ ਦਾ ਖਤਰਾ ਹੈ"
        elif "storm" in hazard_lower:
            hazard_text = "ਤੇਜ਼ ਤੂਫ਼ਾਨ ਆਉਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        elif "heat" in hazard_lower:
            hazard_text = "ਬਹੁਤ ਜ਼ਿਆਦਾ ਗਰਮੀ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        elif hazard in ["ਭਾਰੀ ਮੀਂਹ", "ਭਾਰੀ ਬਾਰਿਸ਼"]:
            hazard_text = "ਭਾਰੀ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        elif hazard == "ਹੜ੍ਹ":
            hazard_text = "ਹੜ੍ਹ ਆਉਣ ਦਾ ਖਤਰਾ ਹੈ"
        elif hazard in ["ਤੂਫ਼ਾਨ", "ਤੇਜ਼ ਤੂਫ਼ਾਨ"]:
            hazard_text = "ਤੇਜ਼ ਤੂਫ਼ਾਨ ਆਉਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        elif hazard in ["ਗਰਮੀ", "ਬਹੁਤ ਜ਼ਿਆਦਾ ਗਰਮੀ"]:
            hazard_text = "ਬਹੁਤ ਜ਼ਿਆਦਾ ਗਰਮੀ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ"
        else:
            hazard_text = f"{hazard} ਦਾ ਖਤਰਾ ਹੈ"

        message = (
            f"ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਜੀ। "
            f"ਤੁਹਾਡੇ ਇਲਾਕੇ {location} ਵਿੱਚ "
            f"{eta} ਮਿੰਟਾਂ ਵਿੱਚ {hazard_text}। "
        )

        if actions:
            message += "ਕਿਰਪਾ ਕਰਕੇ ਹੇਠ ਦਿੱਤੀਆਂ ਸਾਵਧਾਨੀਆਂ ਵਰਤੋ। "

            for action in actions:
                action_lower = action.lower()

                if "drainage" in action_lower:
                    message += "ਖੇਤਾਂ ਵਿੱਚ ਪਾਣੀ ਦੀ ਨਿਕਾਸੀ ਦੀ ਜਾਂਚ ਕਰੋ। "

                elif "pesticide" in action_lower:
                    message += "ਕੀਟਨਾਸ਼ਕਾਂ ਦਾ ਛਿੜਕਾਅ ਨਾ ਕਰੋ। "

                else:
                    message += f"{action}। "

        message += "ਸਾਵਧਾਨ ਰਹੋ ਅਤੇ ਸੁਰੱਖਿਅਤ ਰਹੋ।"

        return message

    # -------------------------
    # HINDI
    # -------------------------
    elif language == "hindi":

        hazard_lower = hazard.lower()

        if "rain" in hazard_lower:
            hazard_text = "भारी बारिश होने की संभावना है"
        elif "flood" in hazard_lower:
            hazard_text = "बाढ़ आने का खतरा है"
        elif "storm" in hazard_lower:
            hazard_text = "तेज़ तूफान आने की संभावना है"
        elif "heat" in hazard_lower:
            hazard_text = "बहुत अधिक गर्मी पड़ने की संभावना है"
        else:
            hazard_text = f"{hazard} का खतरा है"

        message = (
            f"नमस्ते जी। "
            f"{location} में लगभग {eta} मिनट में "
            f"{hazard_text}। "
            f"कृपया सावधान रहें। "
        )

        if actions:
            message += "कृपया निम्न सावधानियां बरतें। "

            for action in actions:
                action_lower = action.lower()

                if "drainage" in action_lower:
                    message += "खेतों में पानी की निकासी की जांच करें। "

                elif "pesticide" in action_lower:
                    message += "कीटनाशकों का छिड़काव न करें। "

                else:
                    message += f"{action}। "

        message += "सुरक्षित रहें।"

        return message

    # -------------------------
    # ENGLISH
    # -------------------------
    else:

        message = (
            f"Attention. "
            f"{hazard} is expected in {location} "
            f"within {eta} minutes. "
        )

        if actions:
            message += "Please take the following precautions. "

            for action in actions:
                message += f"{action}. "

        message += "Please stay alert and stay safe."

        return message