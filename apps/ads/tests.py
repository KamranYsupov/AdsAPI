from unittest.mock import patch

from django.core.paginator import Page
from django.db import transaction
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.ads.models import Ad, Category, ExchangeProposal
from apps.ads.forms import AdForm, ExchangeProposalForm


class AdViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.test_user = User.objects.create_user(**self.test_user_data)
        self.test_category = Category.objects.create(
            name='Тестовая категория',
        )
        self.test_ad_data = {
            'title': 'Test Ad',
            'description': 'Test description',
            'category': self.test_category.id,
            'condition': Ad.Condition.NEW
        }

class CreateAdViewTest(AdViewTestCase):
    """Класс для тестирования create_ad view"""
    def setUp(self):
        super().setUp()
        self.url = reverse('ad_create')

    def test_create_ad_view_requires_login(self):
        """Тест проверки требования авторизации для доступа к странице"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_create_ad_view_uses_correct_template(self):
        """Тест для проверки использования правильного шаблона"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ads/ad_form.html')

    def test_create_ad_with_valid_data(self):
        """Тест успешного создания объявления"""
        self.client.login(**self.test_user_data)
        response = self.client.post(self.url, data=self.test_ad_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ad.objects.count(), 1)

        ad = Ad.objects.first()
        self.assertEqual(ad.title, self.test_ad_data['title'])
        self.assertEqual(ad.user, self.test_user)
        self.assertRedirects(response, reverse('ad_detail', kwargs={'ad_id': ad.id}))

    def test_create_ad_with_invalid_data(self):
        """Тест создания объявления c невалидными данными"""
        self.client.login(**self.test_user_data)
        invalid_data = self.test_ad_data.copy()
        invalid_data['title'] = ''

        response = self.client.post(self.url, data=invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ad.objects.count(), 0)


class AdDetailViewTest(AdViewTestCase):
    def setUp(self):
        super().setUp()
        self.test_ad_data['category'] = self.test_category
        self.test_ad_data['user'] = self.test_user
        self.test_ad = Ad.objects.create(**self.test_ad_data)

        self.url = reverse('ad_detail', kwargs={'ad_id': self.test_ad.id})

    def test_ad_detail_view_returns_200(self):
        """Тест успешного отображения существующего объявления"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ad_detail_view_uses_correct_template(self):
        """Тест использования правильного шаблона"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/ad_detail.html')

    def test_ad_detail_view_context(self):
        """Тест правильности данных в контексте"""
        response = self.client.get(self.url)
        self.assertIn('ad', response.context)
        self.assertEqual(response.context['ad'], self.test_ad)

    def test_ad_detail_view_shows_correct_content(self):
        """Тест отображения контента объявления"""
        response = self.client.get(self.url)
        self.assertContains(response, self.test_ad.title)
        self.assertContains(response, self.test_ad.description)
        self.assertContains(response, self.test_ad.get_condition_display())

    def test_ad_detail_view_404_for_nonexistent_ad(self):
        """Тест 404 для несуществующего объявления"""
        invalid_url = reverse('ad_detail', kwargs={'ad_id': 999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_ad_detail_view_category_display(self):
        """Тест отображения категории"""
        response = self.client.get(self.url)
        self.assertContains(response, self.test_category.name)

    def test_ad_detail_view_user_info(self):
        """Тест отображения информации о пользователе"""
        response = self.client.get(self.url)
        self.assertContains(response, self.test_user.username)


class EditAdViewTest(AdViewTestCase):
    def setUp(self):
        super().setUp()
        self.test_ad_data['category'] = self.test_category
        self.test_ad_data['user'] = self.test_user
        self.test_ad = Ad.objects.create(**self.test_ad_data)

        self.other_user_data = {
            'username': 'otheruser',
            'password': 'testpass123'
        }
        self.other_user = User.objects.create_user(**self.other_user_data)
        self.url = reverse('ad_edit', kwargs={'ad_id': self.test_ad.id})
        self.test_edit_add_data = {
            'title': 'Updated Ad',
            'description': 'Updated description',
            'category': self.test_category.id,
            'condition': Ad.Condition.LIKE_NEW
        }

    def test_edit_ad_requires_login(self):
        """Тест проверки требования авторизации для доступа к странице"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_edit_ad_owner_access(self):
        """Тест доступа владельца объявления"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_ad_non_owner_access(self):
        """Тест запрета доступа для не-владельца"""
        self.client.login(**self.other_user_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/403.html')

    def test_edit_ad_uses_correct_template(self):
        """Тест использования правильного шаблона"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/ad_form.html')

    def test_edit_ad_form_in_context(self):
        """Тест наличия формы в контексте"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].instance, self.test_ad)

    def test_successful_ad_update(self):
        """Тест успешного обновления объявления"""
        self.client.login(**self.test_user_data)
        response = self.client.post(self.url, data=self.test_edit_add_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ad_detail', kwargs={'ad_id': self.test_ad.id}))

        updated_ad = Ad.objects.get(id=self.test_ad.id)
        self.assertEqual(updated_ad.title, self.test_edit_add_data['title'])
        self.assertEqual(updated_ad.description, self.test_edit_add_data['description'])
        self.assertEqual(updated_ad.condition, self.test_edit_add_data['condition'])

    def test_edit_ad_with_invalid_data(self):
        """Тест с невалидными данными"""
        self.client.login(**self.test_user_data)
        invalid_data = self.test_edit_add_data.copy()
        invalid_data['title'] = ''

        response = self.client.post(self.url, data=invalid_data)

        self.assertEqual(response.status_code, 200)

        not_updated_ad = Ad.objects.get(id=self.test_ad.id)
        self.assertEqual(not_updated_ad.title, 'Test Ad')


class AdListViewTest(AdViewTestCase):
    def setUp(self):
        super().setUp()
        self.category1 = Category.objects.create(name='Electronics')
        self.category2 = Category.objects.create(name='Books')

        self.ad1 = Ad.objects.create(
            title='iPhone 12',
            description='New iPhone 12 for sale',
            user=self.test_user,
            category=self.category1,
            condition='new',
            is_active=True
        )
        self.ad2 = Ad.objects.create(
            title='Python Book',
            description='Learn Python programming',
            user=self.test_user,
            category=self.category2,
            condition='used',
            is_active=True
        )
        self.inactive_ad = Ad.objects.create(
            title='Inactive Ad',
            description='Should not appear',
            user=self.test_user,
            category=self.category1,
            is_active=False
        )

        self.url = reverse('ad_list')

    def test_ad_list_returns_200(self):
        """Тест успешного отображения списка"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ad_list_template(self):
        """Тест использования правильного шаблона"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/ad_list.html')

    def test_ad_list_context(self):
        """Тест наличия всех необходимых данных в контексте"""
        response = self.client.get(self.url)

        context = response.context
        self.assertIsInstance(context['page_obj'], Page)
        self.assertEqual(list(context['categories']), list(Category.objects.all()))
        self.assertEqual(context['conditions'], Ad.Condition.CHOICES)
        self.assertIsNone(context['query'])
        self.assertIsNone(context['current_category'])
        self.assertEqual(context['current_condition'], (None, None))

    def test_ad_list_only_active(self):
        """Тест, что показываются только активные объявления"""
        response = self.client.get(self.url)
        ads = response.context['page_obj'].object_list
        self.assertEqual(len(ads), 2)
        self.assertNotIn(self.inactive_ad, ads)

    def test_ad_list_search_by_query(self):
        """Тест поиска по текстовому запросу"""
        response = self.client.get(self.url, {'q': 'iPhone'})
        ads = response.context['page_obj'].object_list
        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].title, 'iPhone 12')

    def test_ad_list_filter_by_category(self):
        """Тест фильтрации по категории"""
        response = self.client.get(self.url, {'category': self.category1.id})
        ads = response.context['page_obj'].object_list
        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].category, self.category1)
        self.assertEqual(response.context['current_category'], self.category1)

    def test_ad_list_filter_by_condition(self):
        """Тест фильтрации по состоянию"""
        response = self.client.get(self.url, {'condition': Ad.Condition.NEW})
        ads = response.context['page_obj'].object_list
        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].condition, Ad.Condition.NEW)
        self.assertEqual(response.context['current_condition'][0], Ad.Condition.NEW)

    def test_ad_list_combined_filters(self):
        """Тест комбинированных фильтров"""
        response = self.client.get(self.url, {
            'q': 'Python',
            'category': self.category2.id,
            'condition': 'used'
        })
        ads = response.context['page_obj'].object_list
        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].title, 'Python Book')

    def test_ad_list_pagination(self):
        """Тест пагинации"""
        for i in range(15):
            Ad.objects.create(
                title=f'Test Ad {i}',
                description=f'Description {i}',
                user=self.test_user,
                category=self.category1,
                condition=Ad.Condition.NEW,
                is_active=True
            )

        # Первая страница
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['page_obj']), 10)

        # Вторая страница
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 7)  # 2 исходных + 15 новых - 10 на первой странице

    def test_ad_list_invalid_category(self):
        """Тест обработки несуществующей категории"""
        with self.assertRaises(Category.DoesNotExist):
            self.client.get(self.url, {'category': 999})


class DeleteAdViewTest(AdViewTestCase):
    def setUp(self):
        super().setUp()

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.test_ad_data['category'] = self.test_category
        self.test_ad_data['user'] = self.test_user
        self.test_ad = Ad.objects.create(**self.test_ad_data)

        self.url = reverse('ad_delete', kwargs={'ad_id': self.test_ad.id})

    def test_delete_ad_requires_login(self):
        """"Тест проверки требования авторизации для доступа к странице"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_delete_ad_owner_access(self):
        """Тест доступа владельца объявления"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_ad_non_owner_access(self):
        """Тест запрета доступа для не-владельца"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/403.html')

    def test_delete_ad_uses_correct_template(self):
        """Тест использования правильного шаблона"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/ad_confirm_delete.html')

    def test_delete_ad_context(self):
        """Тест правильности данных в контексте"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertIn('ad', response.context)
        self.assertEqual(response.context['ad'], self.test_ad)

    def test_successful_ad_deletion(self):
        """Тест успешного удаления объявления"""
        self.client.login(**self.test_user_data)
        response = self.client.post(self.url)

        updated_ad = Ad.objects.get(id=self.test_ad.id)
        self.assertFalse(updated_ad.is_active)

    def test_delete_nonexistent_ad(self):
        """Тест удаления несуществующего объявления"""
        self.client.login(**self.test_user_data)
        invalid_url = reverse('ad_delete', kwargs={'ad_id': 999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)


class CreateProposalViewTest(AdViewTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        # Создаем объявления для тестов
        self.ad_sender = Ad.objects.create(
            title='Sender Ad',
            description='description',
            user=self.test_user,
            category=self.test_category,
            is_active=True
        )
        self.ad_receiver = Ad.objects.create(
            title='Receiver Ad',
            description='description',
            user=self.other_user,
            category=self.test_category,
            is_active=True
        )
        self.inactive_ad = Ad.objects.create(
            title='Inactive Ad',
            description='description',
            user=self.other_user,
            category=self.test_category,
            is_active=False
        )

        self.url = reverse('proposal_create')

    def test_create_proposal_requires_login(self):
        """"Тест проверки требования авторизации для доступа к странице"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_create_proposal_uses_correct_template(self):
        """Тест использования правильного шаблона"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/proposal_form.html')

    def test_create_proposal_form_in_context(self):
        """Тест наличия формы в контексте"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ExchangeProposalForm)

    def test_create_proposal_user_ads_in_context(self):
        """Тест наличия объявлений пользователя в контексте"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        self.assertIn('user_ads', response.context)
        self.assertEqual(list(response.context['user_ads']), [self.ad_sender])

    def test_ad_sender_queryset_filtering(self):
        """Тест фильтрации объявлений-отправителей"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual([self.ad_sender], list(form.fields['ad_sender'].queryset))

    def test_ad_receiver_queryset_filtering(self):
        """Тест фильтрации объявлений-получателей"""
        self.client.login(**self.test_user_data)
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertNotIn(self.inactive_ad, form.fields['ad_receiver'].queryset)
        self.assertNotIn(self.ad_sender, form.fields['ad_receiver'].queryset)

    def test_successful_proposal_creation(self):
        """Тест успешного создания предложения"""
        self.client.login(**self.test_user_data)
        data = {
            'ad_sender': self.ad_sender.id,
            'ad_receiver': self.ad_receiver.id,
            'comment': 'Test proposal'
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        # Проверяем создание предложения
        proposal = ExchangeProposal.objects.first()
        self.assertEqual(proposal.ad_sender, self.ad_sender)
        self.assertEqual(proposal.ad_receiver, self.ad_receiver)
        self.assertEqual(proposal.comment, 'Test proposal')
        self.assertEqual(proposal.status, ExchangeProposal.Status.WAITING)

        self.assertRedirects(
            response,
            reverse('proposal_detail', kwargs={'proposal_id': proposal.id})
        )

    def test_create_proposal_with_invalid_data_1(self):
        """Тест с невалидными данными"""
        self.client.login(**self.test_user_data)
        invalid_data = {
            'ad_sender': self.ad_sender.id,
            'ad_receiver': self.ad_sender.id,
            'comment': ''
        }

        response = self.client.post(self.url, data=invalid_data)

        self.assertEqual(response.status_code, 200)

    def test_create_proposal_with_invalid_data_2(self):
        """Тест с невалидными данными"""
        self.client.login(**self.test_user_data)
        invalid_data = {
            'ad_sender': self.ad_receiver.id,
            'ad_receiver': self.ad_receiver.id,
            'comment': ''
        }

        response = self.client.post(self.url, data=invalid_data)

        self.assertEqual(response.status_code, 200)

    def test_create_proposal_with_inactive_ad(self):
        """Тест с неактивным объявлением"""
        self.client.login(**self.test_user_data)
        data = {
            'ad_sender': self.ad_sender.id,
            'ad_receiver': self.inactive_ad.id,
            'comment': 'Test'
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)


class ExchangeProposalListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Категория 1',
        )

        self.ad1 = Ad.objects.create(
            title='Ad 1',
            user=self.user1,
            category=self.category,
            is_active=True
        )
        self.ad2 = Ad.objects.create(
            title='Ad 2',
            user=self.user2,
            category=self.category,
            is_active=True
        )
        self.ad3 = Ad.objects.create(
            title='Ad 3',
            user=self.user1,
            category=self.category,
            is_active=True
        )
        self.ad4 = Ad.objects.create(
            title='Ad 4',
            user=self.user2,
            category=self.category,
            is_active=True
        )
        self.ad5 = Ad.objects.create(
            title='Ad 6',
            user=self.user1,
            category=self.category,
            is_active=True
        )
        self.ad6 = Ad.objects.create(
            title='Ad 6',
            user=self.user2,
            category=self.category,
            is_active=True
        )

        self.proposal1 = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            status=ExchangeProposal.Status.WAITING
        )
        self.proposal2 = ExchangeProposal.objects.create(
            ad_sender=self.ad4,
            ad_receiver=self.ad3,
            status=ExchangeProposal.Status.ACCEPTED
        )
        self.proposal3 = ExchangeProposal.objects.create(
            ad_sender=self.ad5,
            ad_receiver=self.ad6,
            status=ExchangeProposal.Status.REJECTED
        )

        self.other_ad = Ad.objects.create(
            title='Other Ad',
            user=self.user3,
            category=self.category,
            is_active=True
        )
        self.unrelated_proposal = ExchangeProposal.objects.create(
            ad_sender=self.other_ad,
            ad_receiver=self.ad2,
            status=ExchangeProposal.Status.WAITING
        )

        self.url = reverse('proposal_list')

    def test_exchange_proposal_list_requires_login(self):
        """"Тест проверки требования авторизации для доступа к странице"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_exchange_proposal_list_returns_200(self):
        """Тест успешного отображения списка"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_exchange_proposal_list_template(self):
        """Тест использования правильного шаблона"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'ads/proposal_list.html')

    def test_exchange_proposal_list_context(self):
        """Тест наличия всех необходимых данных в контексте"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url)

        context = response.context
        self.assertIn('proposals', context)
        self.assertIn('status_choices', context)
        self.assertEqual(
            list(context['status_choices']),
            list(ExchangeProposal.Status.CHOICES)
        )

    def test_exchange_proposal_list_only_user_related(self):
        """Тест для проверки показа только относящиеся к пользователю предложения"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url)
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 3)
        self.assertIn(self.proposal1, proposals)
        self.assertIn(self.proposal2, proposals)
        self.assertIn(self.proposal3, proposals)
        self.assertNotIn(self.unrelated_proposal, proposals)

    def test_exchange_proposal_list_filter_by_status(self):
        """Тест фильтрации по статусу"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(
            self.url,
            {'status': ExchangeProposal.Status.WAITING}
        )
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].status, ExchangeProposal.Status.WAITING)

    def test_exchange_proposal_list_filter_by_sender(self):
        """Тест фильтрации по отправителю"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {'sender': 'user2'})
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].ad_sender.user.username, 'user2')

    def test_exchange_proposal_list_filter_by_receiver(self):
        """Тест фильтрации по получателю"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {'receiver': 'user2'})
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 2)
        self.assertEqual(proposals[0].ad_receiver.user.username, 'user2')
        self.assertEqual(proposals[1].ad_receiver.user.username, 'user2')

    def test_exchange_proposal_list_combined_filters(self):
        """Тест комбинированных фильтров"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {
            'status': 'accepted',
            'sender': 'user2',
            'receiver': 'user1'
        })
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].status, 'accepted')
        self.assertEqual(proposals[0].ad_sender.user.username, 'user2')
        self.assertEqual(proposals[0].ad_receiver.user.username, 'user1')

    def test_exchange_proposal_list_invalid_status(self):
        """Тест обработки несуществующего статуса"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {'status': 'invalid'})
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 0)

    def test_exchange_proposal_list_invalid_sender(self):
        """Тест обработки несуществующего отправителя"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {'sender': 'nonexistent'})
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 0)

    def test_exchange_proposal_list_invalid_receiver(self):
        """Тест обработки несуществующего получателя"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(self.url, {'receiver': 'nonexistent'})
        proposals = response.context['proposals'].object_list

        self.assertEqual(len(proposals), 0)


class ProposalDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем пользователей
        self.sender = User.objects.create_user(
            username='sender',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )

        # Создаем категорию
        self.category = Category.objects.create(
            name='Категория 1',
        )

        # Создаем объявления
        self.ad1 = Ad.objects.create(
            title='Ad 1',
            user=self.sender,
            category=self.category,
            is_active=True
        )
        self.ad2 = Ad.objects.create(
            title='Ad 2',
            user=self.receiver,
            category=self.category,
            is_active=True
        )
        self.ad3 = Ad.objects.create(
            title='Ad 3',
            user=self.sender,
            category=self.category,
            is_active=True
        )
        self.ad4 = Ad.objects.create(
            title='Ad 4',
            user=self.receiver,
            category=self.category,
            is_active=True
        )
        self.ad5 = Ad.objects.create(
            title='Ad 6',
            user=self.sender,
            category=self.category,
            is_active=True
        )
        self.ad6 = Ad.objects.create(
            title='Ad 6',
            user=self.receiver,
            category=self.category,
            is_active=True
        )

        # Создаем предложения с разными статусами
        self.waiting_proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            status=ExchangeProposal.Status.WAITING,
            comment='Waiting proposal'
        )
        self.accepted_proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad3,
            ad_receiver=self.ad4,
            status=ExchangeProposal.Status.ACCEPTED,
            comment='Accepted proposal'
        )
        self.rejected_proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad5,
            ad_receiver=self.ad6,
            status=ExchangeProposal.Status.REJECTED,
            comment='Rejected proposal'
        )

    def test_proposal_detail_requires_login(self):
        """"Тест проверки требования авторизации для доступа к странице"""
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={url}'
        )

    def test_proposal_detail_sender_access(self):
        """Тест доступа для отправителя предложения"""
        self.client.login(username='sender', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ads/proposal_detail.html')

    def test_proposal_detail_receiver_access(self):
        """Тест доступа для получателя предложения"""
        self.client.login(username='receiver', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ads/proposal_detail.html')

    def test_proposal_detail_unauthorized_access(self):
        """Тест запрета доступа для постороннего пользователя"""
        self.client.login(username='other', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/403.html')

    def test_proposal_detail_context_data(self):
        """Тест данных в контексте"""
        self.client.login(username='receiver', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)

        context = response.context
        self.assertEqual(context['proposal'], self.waiting_proposal)
        self.assertTrue(context['can_respond'])

    def test_can_respond_flag_for_waiting_proposal(self):
        """Тест флага can_respond для ожидающего предложения"""
        # Получатель должен иметь возможность ответить
        self.client.login(username='receiver', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})
        response = self.client.get(url)
        self.assertTrue(response.context['can_respond'])

        # Отправитель не должен иметь возможность ответить
        self.client.login(username='sender', password='testpass123')
        response = self.client.get(url)
        self.assertFalse(response.context['can_respond'])

    def test_can_respond_flag_for_accepted_proposal(self):
        """Тест флага can_respond для принятого предложения"""
        self.client.login(username='receiver', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.accepted_proposal.id})
        response = self.client.get(url)
        self.assertFalse(response.context['can_respond'])

    def test_can_respond_flag_for_rejected_proposal(self):
        """Тест флага can_respond для отклоненного предложения"""
        self.client.login(username='receiver', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.rejected_proposal.id})
        response = self.client.get(url)
        self.assertFalse(response.context['can_respond'])

    def test_proposal_detail_nonexistent_proposal(self):
        """Тест несуществующего предложения"""
        self.client.login(username='sender', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_proposal_detail_select_related_optimization(self):
        """Тест оптимизации запросов с select_related"""
        self.client.login(username='sender', password='testpass123')
        url = reverse('proposal_detail', kwargs={'proposal_id': self.waiting_proposal.id})

        with self.assertNumQueries(3):  # Проверяем количество SQL запросов
            self.client.get(url)


class UpdateProposalViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.sender = User.objects.create_user(
            username='sender',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )

        # Создаем категорию
        self.category = Category.objects.create(
            name='Категория 1',
        )

        self.sender_ad = Ad.objects.create(
            title='Sender Ad',
            user=self.sender,
            category=self.category,
            is_active=True
        )
        self.receiver_ad = Ad.objects.create(
            title='Receiver Ad',
            user=self.receiver,
            category=self.category,
            is_active=True
        )

        self.proposal = ExchangeProposal.objects.create(
            ad_sender=self.sender_ad,
            ad_receiver=self.receiver_ad,
            status=ExchangeProposal.Status.WAITING
        )

        self.url = reverse('proposal_update', kwargs={'proposal_id': self.proposal.id})

    def test_update_proposal_requires_login(self):
        """"Тест проверки требования авторизации для доступа к странице"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/accounts/login/?next={self.url}'
        )

    def test_update_proposal_receiver_access(self):
        """Тест доступа для получателя предложения"""
        self.client.login(username='receiver', password='testpass123')
        response = self.client.post(
            self.url,
            {'status': ExchangeProposal.Status.ACCEPTED}
        )
        self.assertEqual(response.status_code, 302)

    def test_update_proposal_unauthorized_access(self):
        """Тест запрета доступа для посторонних пользователей"""
        # Тест для отправителя (не может изменять статус)
        self.client.login(username='sender', password='testpass123')
        response = self.client.post(
            self.url,
            {'status': ExchangeProposal.Status.ACCEPTED},
        )
        self.assertEqual(response.status_code, 403)

        # Тест для постороннего пользователя
        self.client.login(username='other', password='testpass123')
        response = self.client.post(
            self.url,
            {'status': ExchangeProposal.Status.ACCEPTED}
        )
        self.assertEqual(response.status_code, 403)

    def test_update_proposal_valid_status(self):
        """Тест обновления с валидным статусом"""
        self.client.login(username='receiver', password='testpass123')

        for status, _ in ExchangeProposal.Status.CHOICES:
            response = self.client.post(self.url, {'status': status})
            self.assertEqual(response.status_code, 302)

            # Проверяем обновление статуса
            updated_proposal = ExchangeProposal.objects.get(id=self.proposal.id)
            self.assertEqual(updated_proposal.status, status)

            # Проверяем редирект
            self.assertRedirects(
                response,
                reverse('proposal_detail', kwargs={'proposal_id': self.proposal.id})
            )

    def test_update_proposal_invalid_status(self):
        """Тест с невалидным статусом"""
        self.client.login(username='receiver', password='testpass123')
        response = self.client.post(self.url, {'status': 'invalid_status'})

        # Проверяем, что статус не изменился
        updated_proposal = ExchangeProposal.objects.get(id=self.proposal.id)
        self.assertEqual(updated_proposal.status, ExchangeProposal.Status.WAITING)

        # Проверяем редирект
        self.assertEqual(response.status_code, 302)

    def test_update_proposal_accept_deactivates_ads(self):
        """Тест деактивации объявлений при принятии предложения"""
        self.client.login(username='receiver', password='testpass123')
        response = self.client.post(
            self.url,
            {'status': ExchangeProposal.Status.ACCEPTED}
        )

        # Проверяем, что объявления деактивированы
        updated_sender_ad = Ad.objects.get(id=self.sender_ad.id)
        updated_receiver_ad = Ad.objects.get(id=self.receiver_ad.id)
        self.assertFalse(updated_sender_ad.is_active)
        self.assertFalse(updated_receiver_ad.is_active)

    def test_update_proposal_atomic_transaction(self):
        """Тест атомарности транзакции"""
        self.client.login(username='receiver', password='testpass123')

        # Создаем мок для проверки транзакции
        with transaction.atomic(), self.assertRaises(Exception):
            # Имитируем ошибку после обновления статуса, но до деактивации объявлений
            with patch.object(ExchangeProposal, 'save', side_effect=Exception('Test')):
                response = self.client.post(self.url, {'status': 'accepted'})

            # Проверяем, что статус не изменился
            updated_proposal = ExchangeProposal.objects.get(id=self.proposal.id)
            self.assertEqual(updated_proposal.status, ExchangeProposal.Status.WAITING)

            # Проверяем, что объявления остались активными
            updated_sender_ad = Ad.objects.get(id=self.sender_ad.id)
            updated_receiver_ad = Ad.objects.get(id=self.receiver_ad.id)
            self.assertTrue(updated_sender_ad.is_active)
            self.assertTrue(updated_receiver_ad.is_active)

    def test_update_proposal_nonexistent_proposal(self):
        """Тест несуществующего предложения"""
        self.client.login(username='receiver', password='testpass123')
        invalid_url = reverse('proposal_update', kwargs={'proposal_id': 999})
        response = self.client.post(
            invalid_url,
            {'status': ExchangeProposal.Status.ACCEPTED}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_proposal_get_request(self):
        """Тест GET-запроса (должен редиректить)"""
        self.client.login(username='receiver', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('proposal_detail', kwargs={'proposal_id': self.proposal.id})
        )