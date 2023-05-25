import asyncio

# There are many different radio libraries but they all have the same API
from zigpy_deconz.zigbee.application import ControllerApplication


class MainListener:
    """
    Contains callbacks that zigpy will call whenever something happens.
    Look for `listener_event` in the Zigpy source or just look at the logged warnings.
    """

    def __init__(self, application):
        self.application = application

    def device_joined(self, device):
        print(f"Device joined: {device}")

    def attribute_updated(self, device, cluster, attribute_id, value):
        print(f"Received an attribute update {attribute_id}={value}"
              f" on cluster {cluster} from device {device}")


async def main():
    app = ControllerApplication(ControllerApplication.SCHEMA({
        #"database_path": "/path/to/zigbee.db",
        "device": {
            "path": "COM3",
        }
    }))

    listener = MainListener(app)
    app.add_listener(listener)

    await app.startup(auto_form=True)

    # Permit joins for a minute
    await app.permit(60)
    await asyncio.sleep(60)

    # Just run forever
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())