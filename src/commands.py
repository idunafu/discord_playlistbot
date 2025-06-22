"""スラッシュコマンド定義モジュール
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands


async def setup_commands(bot: commands.Bot) -> None:
    """スラッシュコマンドを設定"""

    @bot.tree.command(name="setting", description="Botの設定を行います")
    @app_commands.describe(
        action="実行する設定アクション",
        channel="設定するチャンネル（未指定の場合は現在のチャンネル）",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="monitor", value="monitor"),
        app_commands.Choice(name="notification", value="notification"),
        app_commands.Choice(name="show", value="show"),
    ])
    async def setting(
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        channel: discord.TextChannel | None = None,
    ) -> None:
        """設定コマンド"""
        if not interaction.guild:
            await interaction.response.send_message("このコマンドはサーバー内でのみ使用できます。", ephemeral=True)
            return

        # 管理者権限チェック
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("このコマンドを使用する権限がありません。", ephemeral=True)
            return

        target_channel = channel or interaction.channel

        if action.value == "monitor":
            await _set_monitor_channel(interaction, target_channel, bot)
        elif action.value == "notification":
            await _set_notification_channel(interaction, target_channel, bot)
        elif action.value == "show":
            await _show_settings(interaction, bot)

    @bot.tree.command(name="backlog", description="過去のメッセージからURLを処理します")
    @app_commands.describe(count="処理するメッセージ数（1-100）")
    async def backlog(interaction: discord.Interaction, count: int) -> None:
        """過去ログ処理コマンド"""
        if not interaction.guild:
            await interaction.response.send_message("このコマンドはサーバー内でのみ使用できます。", ephemeral=True)
            return

        # 管理者権限チェック
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("このコマンドを使用する権限がありません。", ephemeral=True)
            return

        if count < 1 or count > 100:
            await interaction.response.send_message("メッセージ数は1から100の間で指定してください。", ephemeral=True)
            return

        await _process_backlog(interaction, count, bot)

    @bot.tree.command(name="help", description="Botの使い方を表示します")
    async def help_command(interaction: discord.Interaction) -> None:
        """ヘルプコマンド"""
        embed = discord.Embed(
            title="🎵 Discord音楽リンク収集Bot",
            description="YouTubeとSoundCloudのリンクを自動でプレイリストに追加します",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="📝 設定コマンド",
            value=(
                "`/setting monitor [チャンネル]` - 監視するチャンネルを設定\n"
                "`/setting notification [チャンネル]` - 通知チャンネルを設定\n"
                "`/setting show` - 現在の設定を表示"
            ),
            inline=False,
        )

        embed.add_field(
            name="🔄 操作コマンド",
            value="`/backlog [件数]` - 過去のメッセージを遡って処理",
            inline=False,
        )

        embed.add_field(
            name="🎯 対応URL",
            value=(
                "• YouTube: `youtube.com/watch`, `youtu.be`\n"
                "• YouTube Music: `music.youtube.com`\n"
                "• SoundCloud: `soundcloud.com` （設定済みの場合のみ）"
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ 機能",
            value=(
                "• 自動リンク検出・プレイリスト追加\n"
                "• 重複チェック\n"
                "• 処理結果通知\n"
                "• OAuth 2.1 (PKCE) 認証"
            ),
            inline=False,
        )

        embed.set_footer(text="管理者権限が必要なコマンドがあります")

        await interaction.response.send_message(embed=embed)


async def _set_monitor_channel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    bot: commands.Bot,
) -> None:
    """監視チャンネルを設定"""
    try:
        await bot.db_manager.set_monitored_channel(interaction.guild.id, channel.id)

        embed = discord.Embed(
            title="✅ 監視チャンネル設定完了",
            description=f"監視対象チャンネル: {channel.mention}",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)
        logging.info(f"Guild {interaction.guild.id}: 監視チャンネル設定 -> {channel.id}")

    except Exception as e:
        logging.exception(f"監視チャンネル設定エラー: {e}")
        await interaction.response.send_message("設定の保存に失敗しました。", ephemeral=True)


async def _set_notification_channel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    bot: commands.Bot,
) -> None:
    """通知チャンネルを設定"""
    try:
        await bot.db_manager.set_notification_channel(interaction.guild.id, channel.id)

        embed = discord.Embed(
            title="✅ 通知チャンネル設定完了",
            description=f"通知チャンネル: {channel.mention}",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)
        logging.info(f"Guild {interaction.guild.id}: 通知チャンネル設定 -> {channel.id}")

    except Exception as e:
        logging.exception(f"通知チャンネル設定エラー: {e}")
        await interaction.response.send_message("設定の保存に失敗しました。", ephemeral=True)


async def _show_settings(interaction: discord.Interaction, bot: commands.Bot) -> None:
    """現在の設定を表示"""
    try:
        settings = await bot.db_manager.get_server_settings(interaction.guild.id)

        embed = discord.Embed(
            title="⚙️ 現在の設定",
            color=discord.Color.blue(),
        )

        # 監視チャンネル
        monitor_channel_id = settings.get("monitored_channel_id")
        if monitor_channel_id:
            monitor_channel = interaction.guild.get_channel(monitor_channel_id)
            monitor_text = monitor_channel.mention if monitor_channel else f"ID: {monitor_channel_id} (チャンネルが見つかりません)"
        else:
            monitor_text = "未設定"

        embed.add_field(
            name="📺 監視チャンネル",
            value=monitor_text,
            inline=False,
        )

        # 通知チャンネル
        notification_channel_id = settings.get("notification_channel_id")
        if notification_channel_id:
            notification_channel = interaction.guild.get_channel(notification_channel_id)
            notification_text = notification_channel.mention if notification_channel else f"ID: {notification_channel_id} (チャンネルが見つかりません)"
        else:
            notification_text = "未設定"

        embed.add_field(
            name="🔔 通知チャンネル",
            value=notification_text,
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        logging.exception(f"設定表示エラー: {e}")
        await interaction.response.send_message("設定の取得に失敗しました。", ephemeral=True)


async def _process_backlog(
    interaction: discord.Interaction,
    count: int,
    bot: commands.Bot,
) -> None:
    """過去ログを処理"""
    try:
        # まず応答してからバックグラウンドで処理
        await interaction.response.send_message(f"📚 過去{count}件のメッセージの処理を開始します...")

        # 監視チャンネルを取得
        monitored_channel_id = await bot.db_manager.get_monitored_channel(interaction.guild.id)
        if not monitored_channel_id:
            await interaction.followup.send("❌ 監視チャンネルが設定されていません。先に `/setting monitor` で設定してください。")
            return

        channel = interaction.guild.get_channel(monitored_channel_id)
        if not channel:
            await interaction.followup.send("❌ 監視チャンネルが見つかりません。")
            return

        youtube_processed = 0
        soundcloud_processed = 0
        soundcloud_skipped = 0
        total_urls = 0

        # 過去のメッセージを取得して処理
        async for message in channel.history(limit=count):
            if message.author.bot:
                continue

            urls = bot.url_extractor.extract_urls(message.content)
            total_urls += len(urls)

            for url in urls:
                # 重複チェック
                if await bot.db_manager.is_url_processed(interaction.guild.id, url):
                    continue

                service_type = bot.url_extractor.identify_service(url)

                if service_type == "youtube":
                    success = await bot.youtube_service.add_to_playlist(url)
                    if success:
                        await bot.db_manager.mark_url_processed(
                            interaction.guild.id, url, service_type,
                        )
                        youtube_processed += 1

                elif service_type == "soundcloud":
                    if bot.soundcloud_service:
                        success = await bot.soundcloud_service.add_to_playlist(url)
                        if success:
                            await bot.db_manager.mark_url_processed(
                                interaction.guild.id, url, service_type,
                            )
                            soundcloud_processed += 1
                    else:
                        soundcloud_skipped += 1

        # 結果報告
        total_processed = youtube_processed + soundcloud_processed
        embed = discord.Embed(
            title="✅ 過去ログ処理完了",
            description=f"処理結果: {total_processed}件のURLを新しくプレイリストに追加しました",
            color=discord.Color.green(),
        )
        embed.add_field(name="総URL数", value=f"{total_urls}件", inline=True)
        embed.add_field(name="YouTube追加", value=f"{youtube_processed}件", inline=True)
        embed.add_field(name="SoundCloud追加", value=f"{soundcloud_processed}件", inline=True)

        if soundcloud_skipped > 0:
            embed.add_field(
                name="SoundCloudスキップ",
                value=f"{soundcloud_skipped}件（API未設定）",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        logging.exception(f"過去ログ処理エラー: {e}")
        await interaction.followup.send(f"❌ 過去ログ処理中にエラーが発生しました: {e!s}")
