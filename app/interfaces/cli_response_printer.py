from __future__ import annotations

from app.models.conversation_response import ConversationResponse


def print_conversation_response(
    response: ConversationResponse,
) -> None:

    if response.status == "NEEDS_INPUT":

        print(
            f"\nQuestion:\n{response.question}\n"
        )

        return

    if response.status == "READY":

        if response.message is not None:
            print(response.message)

        if response.hotel_contexts:

            print("\nHotel Contexts:")

            for context in response.hotel_contexts:

                hotel = context.hotel

                print(f"\n{hotel.name}")

                if context.distance_km is not None:
                    print(
                        f"Distance: "
                        f"{context.distance_km:.2f} km"
                    )
                else:
                    print("Distance: unavailable")

                if context.price_utility is not None:
                    print(
                        f"Price utility: "
                        f"{context.price_utility:.4f}"
                    )

                if context.rating_utility is not None:
                    print(
                        f"Rating utility: "
                        f"{context.rating_utility:.4f}"
                    )

        return

    print(
        f"Unknown response status: {response.status}"
    )