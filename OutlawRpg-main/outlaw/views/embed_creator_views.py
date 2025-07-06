import discord
from discord import ui, ButtonStyle, Interaction, Embed, Color
from datetime import datetime


# Define Modal Classes at the top level so they can be easily referenced
class AddFieldModal(ui.Modal, title="Adicionar Campo ao Embed"):
    def __init__(self):
        super().__init__(timeout=300)
        self.field_name = ui.TextInput(
            label="Nome do Campo",
            placeholder="Ex: Requisitos, Horário",
            max_length=256,
            required=True,
        )
        self.field_value = ui.TextInput(
            label="Valor do Campo",
            placeholder="Ex: Nível 10+, Sábado 19h",
            style=discord.TextStyle.paragraph,
            required=True,
        )
        self.field_inline = ui.TextInput(
            label="Campo na mesma linha? (sim/não)",
            placeholder="Padrão é 'não'.",
            max_length=3,
            required=False,
        )
        self.add_item(self.field_name)
        self.add_item(self.field_value)
        self.add_item(self.field_inline)

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        self.stop()  # Stops the modal


class BasicInfoModal(ui.Modal, title="Editar Título e Descrição"):
    def __init__(self, current_title, current_description):
        super().__init__(timeout=300)
        self.title_input = ui.TextInput(
            label="Novo Título",
            default=current_title,
            max_length=256,
            required=True,
        )
        self.description_input = ui.TextInput(
            label="Nova Descrição",
            default=current_description,
            style=discord.TextStyle.paragraph,
            required=False,
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        self.stop()  # Stops the modal


class MediaModal(ui.Modal, title="Editar Mídia e Cores"):
    def __init__(
        self,
        current_thumb,
        current_image,
        current_color_hex,
        current_author_name,
        current_author_icon,
    ):
        super().__init__(timeout=300)
        self.thumbnail_input = ui.TextInput(
            label="URL da Miniatura (Thumbnail)",
            placeholder="Cole a URL da imagem aqui",
            default=current_thumb or "",
            required=False,
        )
        self.image_input = ui.TextInput(
            label="URL da Imagem Principal",
            placeholder="Cole a URL da imagem aqui",
            default=current_image or "",
            required=False,
        )
        self.color_input = ui.TextInput(
            label="Cor Hexadecimal (Ex: #FF00FF)",
            placeholder="Ex: #FF00FF",
            default=current_color_hex or "",
            max_length=7,
            required=False,
        )
        self.author_name_input = ui.TextInput(
            label="Nome do Autor (opcional)",
            placeholder="Ex: Equipe Outlaws",
            default=current_author_name or "",
            required=False,
        )
        self.author_icon_input = ui.TextInput(
            label="URL do Ícone do Autor (opcional)",
            placeholder="URL do avatar do autor",
            default=current_author_icon or "",
            required=False,
        )
        self.add_item(self.thumbnail_input)
        self.add_item(self.image_input)
        self.add_item(self.color_input)
        self.add_item(self.author_name_input)
        self.add_item(self.author_icon_input)

    async def on_submit(self, modal_interaction: Interaction):
        # The parent view will handle the embed update
        self.stop()  # Stops the modal


# The main EmbedCreatorView class
class EmbedCreatorView(ui.View):
    def __init__(self, initial_embed: Embed, author_id: int):
        super().__init__(timeout=600)
        self.embed = initial_embed
        self.author_id = author_id
        self.fields_added = 0
        self.message = None  # To store the original ephemeral message for editing

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(
                    content="Tempo limite para edição do embed atingido.", view=self
                )
        except discord.HTTPException:
            pass

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Apenas o criador do embed pode interagir com este menu.",
                ephemeral=True,
            )
            return False
        return True

    @ui.button(label="Editar Título/Descrição", style=ButtonStyle.primary, emoji="✍️")
    async def edit_basic_info(self, interaction: Interaction, button: ui.Button):
        # Use the top-level BasicInfoModal
        modal = BasicInfoModal(
            self.embed.title or "",
            self.embed.description or "",
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.is_submitted():
            self.embed.title = modal.title_input.value
            self.embed.description = modal.description_input.value or None
            await self.message.edit(embed=self.embed, view=self)

    @ui.button(label="Adicionar Campo", style=ButtonStyle.secondary, emoji="➕")
    async def add_field(self, interaction: Interaction, button: ui.Button):
        if self.fields_added >= 10:
            await interaction.response.send_message(
                "Você atingiu o limite de 10 campos por embed.", ephemeral=True
            )
            return

        # Use the top-level AddFieldModal
        modal = AddFieldModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.is_submitted() and modal.field_name.value and modal.field_value.value:
            name = modal.field_name.value
            value = modal.field_value.value
            inline = (
                modal.field_inline.value.lower() == "sim"
                if modal.field_inline.value
                else False
            )
            self.embed.add_field(name=name, value=value, inline=inline)
            self.fields_added += 1
            await self.message.edit(embed=self.embed, view=self)
        else:
            await interaction.followup.send(
                "Nenhum campo foi adicionado.", ephemeral=True
            )

    @ui.button(label="Editar Imagens/Cores", style=ButtonStyle.secondary, emoji="🖼️")
    async def edit_media(self, interaction: Interaction, button: ui.Button):
        current_thumb = self.embed.thumbnail.url if self.embed.thumbnail else None
        current_image = self.embed.image.url if self.embed.image else None
        current_color_hex = str(self.embed.color) if self.embed.color else ""
        current_author_name = self.embed.author.name if self.embed.author else None
        current_author_icon = self.embed.author.icon_url if self.embed.author else None

        # Use the top-level MediaModal
        modal = MediaModal(
            current_thumb,
            current_image,
            current_color_hex,
            current_author_name,
            current_author_icon,
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.is_submitted():
            thumb_url = modal.thumbnail_input.value.strip() or None
            self.embed.set_thumbnail(url=thumb_url)

            image_url = modal.image_input.value.strip() or None
            self.embed.set_image(url=image_url)

            if modal.color_input.value:
                try:
                    self.embed.color = Color.from_str(modal.color_input.value)
                except ValueError:
                    await interaction.followup.send(
                        "Cor hexadecimal inválida. Use o formato #RRGGBB.",
                        ephemeral=True,
                    )
                    return
            else:
                self.embed.color = Color.blue()

            author_name = modal.author_name_input.value.strip()
            author_icon = modal.author_icon_input.value.strip() or None
            if author_name:
                self.embed.set_author(name=author_name, icon_url=author_icon)
            else:
                self.embed.remove_author()

            await self.message.edit(embed=self.embed, view=self)

    @ui.button(label="Limpar Campos", style=ButtonStyle.danger, emoji="🧹")
    async def clear_fields(self, interaction: Interaction, button: ui.Button):
        self.embed.clear_fields()
        self.fields_added = 0
        await self.message.edit(embed=self.embed, view=self)

    @ui.button(label="Enviar Embed", style=ButtonStyle.success, emoji="✅", row=2)
    async def send_embed(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message("Embed enviado!", ephemeral=True)
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.HTTPException:
            pass

        try:
            await interaction.channel.send(embed=self.embed)
        except discord.Forbidden:
            await interaction.followup.send(
                "Não tenho permissão para enviar o embed neste canal.", ephemeral=True
            )
        self.stop()
