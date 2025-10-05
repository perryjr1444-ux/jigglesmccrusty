import asyncio


class RouterConnector:
    """
    Vendor-agnostic router helper. For many home routers the only reliable
    remote interface is the local admin page reachable over LAN.
    The Endpoint Helper (see § 9) can invoke this connector via gRPC
    when the user grants temporary admin credentials.
    """

    async def call(self, payload: dict):
        op = payload["__operation"]
        if op == "factory_reset":
            # Expect payload to contain the router IP and admin credentials (already encrypted)
            ip = payload["router_ip"]
            enc_user = payload["admin_user_enc"]
            enc_pass = payload["admin_pass_enc"]

            # Decrypt locally – the helper runs on the user’s device, never sends plaintext
            from utils.crypto import decrypt_payload

            user = decrypt_payload(enc_user).decode()
            passwd = decrypt_payload(enc_pass).decode()

            # Very naïve example using curl; replace with proper vendor SDK in production
            url = f"https://{ip}/reset"
            cmd = [
                "curl",
                "--insecure",
                "-u",
                f"{user}:{passwd}",
                "-X",
                "POST",
                url,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Router reset failed: {err.decode()}")
            return {"summary": f"Factory reset issued to router {ip}"}
        raise NotImplementedError(f"Unsupported router op {op}")
