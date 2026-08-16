from __future__ import annotations

from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.config import ADMIN_ID, ADMIN_IDS, REWARD_AMOUNT
from bot.database import (
    add_transaction,
    get_all_users,
    get_submission_by_id,
    get_withdraw_request_by_id,
    get_user_by_id,
    get_user_by_telegram_id,
    get_pending_uid_submissions,
    get_pending_withdrawals,
    get_stats_summary,
    log_action,
    set_balance,
    update_submission_status,
    update_withdraw_request_status,
)
from bot.utils.logging import setup_logging

logger = setup_logging()

REJECTION_REASONS = [
    "UID was not created using referral code HELAL8",
    "Required trading volume has not been completed",
    "Required deposit has not been completed",
]


async def is_admin(update: Update) -> bool:
    if not update.effective_user:
        return False
    return update.effective_user.id in ADMIN_IDS or update.effective_user.id == ADMIN_ID


async def notify_admin_of_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, submission_id: int, uid: str) -> None:
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user:
        return
    submission = get_submission_by_id(submission_id)
    submission_date = submission["created_at"] if submission else user["created_at"]
    profile_link = f"https://t.me/{user['username']}" if user['username'] else f"tg://user?id={user['telegram_id']}"
    text = (
        f"New UID Submission\n"
        f"Submission ID: {submission_id}\n"
        f"UID Submitted: {uid}\n"
        f"User Details:\n"
        f"Full Name: {user['full_name'] or 'N/A'}\n"
        f"Username: {user['username'] or 'N/A'}\n"
        f"Telegram ID: {user['telegram_id']}\n"
        f"Profile Link: {profile_link}\n"
        f"Submission Date: {submission_date}\n"
        f"Current Status: Pending"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_uid:{submission_id}")],
            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_uid:{submission_id}")],
        ]
    )
    for admin_id in (ADMIN_IDS or {ADMIN_ID}):
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
        except Exception as exc:
            logger.error("Failed to notify admin %s of submission %s: %s", admin_id, submission_id, exc)


async def notify_admin_of_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, amount: float, info: str) -> None:
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user:
        return
    text = (
        f"New Withdrawal Request\n"
        f"User Name: {user['full_name'] or user['username'] or 'N/A'}\n"
        f"Telegram ID: {user['telegram_id']}\n"
        f"Current Balance: ${float(user['balance']):.2f}\n"
        f"Requested Amount: ${amount:.2f}\n"
        f"Withdrawal Information: {info}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Approve Withdrawal", callback_data=f"approve_withdraw:{request_id}")],
            [InlineKeyboardButton("❌ Reject Withdrawal", callback_data=f"reject_withdraw:{request_id}")],
        ]
    )
    for admin_id in (ADMIN_IDS or {ADMIN_ID}):
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
        except Exception as exc:
            logger.error("Failed to notify admin %s of withdrawal %s: %s", admin_id, request_id, exc)


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update):
        await update.message.reply_text("Access denied.")
        return

    text = (update.message.text or "").strip()
    if text == "/stats":
        await handle_stats(update, context)
    elif text == "/users":
        await handle_users(update, context)
    elif text == "/pending":
        await handle_pending(update, context)
    elif text == "/withdrawals":
        await handle_withdrawals(update, context)
    elif text.startswith("/broadcast"):
        await handle_broadcast(update, context)
    else:
        await update.message.reply_text("Unknown admin command.")


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    summary = get_stats_summary()
    await update.message.reply_text(
        f"Stats:\n"
        f"Total Users: {summary['total_users']}\n"
        f"Pending UID Submissions: {summary['pending_uid_submissions']}\n"
        f"Approved UID Submissions: {summary['approved_uid_submissions']}\n"
        f"Rejected UID Submissions: {summary['rejected_uid_submissions']}\n"
        f"Pending Withdrawals: {summary['pending_withdrawals']}\n"
        f"Total Rewards Paid: ${summary['total_rewards_paid']:.2f}"
    )


async def handle_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = get_all_users()
    if not users:
        await update.message.reply_text("No users found.")
        return

    lines = []
    for user in users:
        lines.append(f"{user['full_name'] or user['username'] or 'N/A'} | TG: {user['telegram_id']} | Balance: ${float(user['balance']):.2f}")
    await update.message.reply_text("Users:\n" + "\n".join(lines[:20]))


async def handle_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    submissions = get_pending_uid_submissions()
    if not submissions:
        await update.message.reply_text("No pending submissions.")
        return
    lines = [f"ID {s['id']}: UID {s['uid']} | User {s['user_id']}" for s in submissions]
    await update.message.reply_text("Pending UIDs:\n" + "\n".join(lines[:20]))


async def handle_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    withdrawals = get_pending_withdrawals()
    if not withdrawals:
        await update.message.reply_text("No pending withdrawals.")
        return
    lines = [f"ID {w['id']}: Amount ${float(w['amount']):.2f} | Info: {w['withdrawal_info']}" for w in withdrawals]
    await update.message.reply_text("Pending withdrawals:\n" + "\n".join(lines[:20]))


async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text.split(" ", 1)[1] if " " in update.message.text else ""
    if not message_text:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    users = get_all_users()
    sent = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=int(user["telegram_id"]), text=message_text)
            sent += 1
        except Exception:
            continue
    await update.message.reply_text(f"Broadcast sent to {sent} users.")


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    if not await is_admin(update):
        logger.warning(
            "Non-admin user %s attempted admin callback %s",
            update.effective_user.id if update.effective_user else None,
            update.callback_query.data,
        )
        await update.callback_query.answer("Access denied.", show_alert=True)
        return

    await update.callback_query.answer()
    data = update.callback_query.data or ""

    if data.startswith("approve_uid:"):
        submission_id = int(data.split(":", 1)[1])
        await approve_uid_submission(update, context, submission_id)
        return

    if data.startswith("reject_uid:"):
        submission_id = int(data.split(":", 1)[1])
        if context.chat_data is not None:
            context.chat_data["pending_rejection"] = submission_id
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(reason, callback_data=f"reject_reason:{submission_id}:{index}")] for index, reason in enumerate(REJECTION_REASONS)]
        )
        await update.callback_query.edit_message_text("Select a rejection reason:", reply_markup=keyboard)
        return

    if data.startswith("reject_reason:"):
        parts = data.split(":")
        submission_id = int(parts[1])
        reason_index = int(parts[2])
        if 0 <= reason_index < len(REJECTION_REASONS):
            reason = REJECTION_REASONS[reason_index]
            await reject_uid_submission(update, context, submission_id, reason)
        return

    if data.startswith("reason:"):
        submission_id = context.chat_data.get("pending_rejection") if context.chat_data else None
        reason_index = int(data.split(":", 1)[1])
        if 0 <= reason_index < len(REJECTION_REASONS):
            reason = REJECTION_REASONS[reason_index]
            if submission_id:
                await reject_uid_submission(update, context, int(submission_id), reason)
            else:
                await update.callback_query.edit_message_text(
                    "⚠️ This rejection menu has expired. Please trigger rejection again from a new submission message."
                )
        return

    if data.startswith("approve_withdraw:"):
        request_id = int(data.split(":", 1)[1])
        await approve_withdrawal(update, context, request_id)
        return

    if data.startswith("reject_withdraw:"):
        request_id = int(data.split(":", 1)[1])
        await reject_withdrawal(update, context, request_id)
        return


async def approve_uid_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, submission_id: int) -> None:
    try:
        submission = get_submission_by_id(submission_id)
        if not submission:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ Submission {submission_id} not found.")
            return
        user = get_user_by_id(int(submission["user_id"]))
        if not user:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ User for submission {submission_id} not found.")
            return

        update_submission_status(submission_id, "Approved")
        current_balance = float(user["balance"])
        new_balance = current_balance + REWARD_AMOUNT
        set_balance(int(user["id"]), new_balance)
        add_transaction(int(user["id"]), "reward", REWARD_AMOUNT, f"Approved UID reward for submission {submission_id}")
        log_action(ADMIN_ID, "approve_uid", f"submission_id={submission_id}")

        try:
            await context.bot.send_message(
                chat_id=int(user["telegram_id"]),
                text=f"Your UID has been approved. ${REWARD_AMOUNT:.2f} has been added to your balance.",
            )
        except Exception as exc:
            logger.error("Could not send approval message to user %s: %s", user['telegram_id'], exc)

        if update.callback_query:
            await update.callback_query.edit_message_text(f"✅ Submission {submission_id} approved.")
    except Exception as exc:
        logger.error("Error approving submission %s: %s", submission_id, exc, exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"⚠️ Error approving submission: {exc}")


async def reject_uid_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, submission_id: int, reason: str) -> None:
    try:
        submission = get_submission_by_id(submission_id)
        if not submission:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ Submission {submission_id} not found.")
            return
        user = get_user_by_id(int(submission["user_id"]))
        if not user:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ User for submission {submission_id} not found.")
            return

        update_submission_status(submission_id, "Rejected", reason)
        log_action(ADMIN_ID, "reject_uid", f"submission_id={submission_id}; reason={reason}")

        try:
            await context.bot.send_message(
                chat_id=int(user["telegram_id"]),
                text=f"Your UID submission was rejected.\nReason: {reason}",
            )
        except Exception as exc:
            logger.error("Could not send rejection message to user %s: %s", user['telegram_id'], exc)

        if update.callback_query:
            await update.callback_query.edit_message_text(f"❌ Submission {submission_id} rejected.\nReason: {reason}")
    except Exception as exc:
        logger.error("Error rejecting submission %s: %s", submission_id, exc, exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"⚠️ Error rejecting submission: {exc}")


async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int) -> None:
    try:
        request = get_withdraw_request_by_id(request_id)
        if not request:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ Withdrawal request {request_id} not found.")
            return
        user = get_user_by_id(int(request["user_id"]))
        if not user:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ User for withdrawal {request_id} not found.")
            return
        update_withdraw_request_status(request_id, "Approved")
        deduction_amount = min(float(request["amount"]), float(user["balance"]))
        new_balance = float(user["balance"]) - deduction_amount
        set_balance(int(user["id"]), new_balance)
        add_transaction(int(user["id"]), "withdrawal", -deduction_amount, f"Withdrawal approved for request {request_id}")
        log_action(ADMIN_ID, "approve_withdrawal", f"request_id={request_id}")

        try:
            await context.bot.send_message(
                chat_id=int(user["telegram_id"]),
                text=f"Your withdrawal request has been approved. ${deduction_amount:.2f} has been deducted from your balance.",
            )
        except Exception as exc:
            logger.error("Could not send withdrawal approval to user %s: %s", user['telegram_id'], exc)

        if update.callback_query:
            await update.callback_query.edit_message_text(f"✅ Withdrawal {request_id} approved.")
    except Exception as exc:
        logger.error("Error approving withdrawal %s: %s", request_id, exc, exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"⚠️ Error approving withdrawal: {exc}")


async def reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int) -> None:
    try:
        request = get_withdraw_request_by_id(request_id)
        if not request:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ Withdrawal request {request_id} not found.")
            return
        user = get_user_by_id(int(request["user_id"]))
        if not user:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ User for withdrawal {request_id} not found.")
            return
        update_withdraw_request_status(request_id, "Rejected")
        log_action(ADMIN_ID, "reject_withdrawal", f"request_id={request_id}")

        try:
            await context.bot.send_message(
                chat_id=int(user["telegram_id"]),
                text="Your withdrawal request has been rejected.",
            )
        except Exception as exc:
            logger.error("Could not send withdrawal rejection to user %s: %s", user['telegram_id'], exc)

        if update.callback_query:
            await update.callback_query.edit_message_text(f"❌ Withdrawal {request_id} rejected.")
    except Exception as exc:
        logger.error("Error rejecting withdrawal %s: %s", request_id, exc, exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"⚠️ Error rejecting withdrawal: {exc}")
