SCENARIO_TEMPLATES = [
    {
        "template_id": "welcome_reception",
        "template_name": "Welcome Reception",
        "required_scripts": ["welcome_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "replay", "stop"],
    },
    {
        "template_id": "product_presenter",
        "template_name": "Product Presenter",
        "required_scripts": ["intro_script_id"],
        "required_assets": ["screen_asset_id"],
        "available_tablet_buttons": ["start", "next", "previous", "replay", "stop"],
    },
    {
        "template_id": "event_mc",
        "template_name": "Event MC",
        "required_scripts": ["opening_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "next", "replay", "stop"],
    },
    {
        "template_id": "photo_booth",
        "template_name": "Photo Booth",
        "required_scripts": ["invite_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "replay", "stop"],
    },
    {
        "template_id": "lucky_draw",
        "template_name": "Lucky Draw",
        "required_scripts": ["rules_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "next", "replay", "stop"],
    },
    {
        "template_id": "ai_faq",
        "template_name": "AI FAQ",
        "required_scripts": [],
        "required_assets": [],
        "available_tablet_buttons": ["answer", "replay", "stop"],
    },
    {
        "template_id": "guided_exhibit",
        "template_name": "Guided Exhibit",
        "required_scripts": ["zone_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "next", "previous", "stop"],
    },
    {
        "template_id": "ceremony_launch",
        "template_name": "Ceremony Launch",
        "required_scripts": ["countdown_script_id"],
        "required_assets": [],
        "available_tablet_buttons": ["start", "next", "stop"],
    },
]


def get_template(template_id: str):
    for template in SCENARIO_TEMPLATES:
        if template["template_id"] == template_id:
            return template
    return None


def build_steps(template_id: str, config: dict):
    if template_id == "product_presenter":
        return [
            {
                "step_id": "opening",
                "display_name": "Opening",
                "actions": [
                    {"action_type": "motion", "payload": {"motion_id": "wave"}, "priority": 5},
                    {"action_type": "emoji", "payload": {"emoji_id": 90}, "priority": 5},
                ],
            },
            {
                "step_id": "product_intro",
                "display_name": "Product Introduction",
                "actions": [
                    {
                        "action_type": "screen_video",
                        "payload": {"asset_id": config.get("screen_asset_id")},
                        "priority": 5,
                    },
                    {
                        "action_type": "motion",
                        "payload": {"motion_id": config.get("motion_id", "right_hand_raise")},
                        "priority": 5,
                    },
                    {
                        "action_type": "tts",
                        "payload": {"script_id": config.get("intro_script_id")},
                        "priority": 6,
                    },
                ],
            },
        ]

    script_key_by_template = {
        "welcome_reception": "welcome_script_id",
        "event_mc": "opening_script_id",
        "photo_booth": "invite_script_id",
        "lucky_draw": "rules_script_id",
        "guided_exhibit": "zone_script_id",
        "ceremony_launch": "countdown_script_id",
    }
    script_key = script_key_by_template.get(template_id)
    if script_key:
        return [
            {
                "step_id": "opening",
                "display_name": "Opening",
                "actions": [
                    {"action_type": "motion", "payload": {"motion_id": "wave"}, "priority": 5},
                    {"action_type": "tts", "payload": {"script_id": config.get(script_key)}, "priority": 6},
                ],
            }
        ]

    return [
        {
            "step_id": "default",
            "display_name": "Default",
            "actions": [{"action_type": "tts", "payload": {"text": "Ready."}, "priority": 6}],
        }
    ]
