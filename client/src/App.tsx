import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Button from 'react-bootstrap/Button';
import { TodoListCard } from './components/TodoListCard';
import { SearchPanel } from './components/SearchPanel';
import { DatePanel } from './components/DatePanel';
import { Greeting } from './components/Greeting';
import { I18nProvider } from './i18n';
import { useI18n } from './i18nContext';
import type { Lang } from './i18nContext';

const LANGUAGES: [Lang, string][] = [
    ['ko', '한국어'],
    ['en', 'English'],
];

function LanguageSwitch() {
    const { lang, setLang, t } = useI18n();
    return (
        <div className="text-end pt-3">
            <ButtonGroup size="sm" aria-label={t('language')}>
                {LANGUAGES.map(([value, label]) => (
                    <Button
                        key={value}
                        variant={lang === value ? 'dark' : 'outline-dark'}
                        onClick={() => setLang(value)}
                    >
                        {label}
                    </Button>
                ))}
            </ButtonGroup>
        </div>
    );
}

function Main() {
    const { t } = useI18n();
    return (
        <Container>
            <Row>
                <Col md={{ offset: 3, span: 6 }}>
                    <LanguageSwitch />
                    <Greeting />
                    {/* 탭 전환 시 다시 불러오므로 등록/삭제 결과가 항상 반영된다 */}
                    <Tabs
                        defaultActiveKey="work"
                        className="mb-3"
                        mountOnEnter
                        unmountOnExit
                        fill
                    >
                        <Tab eventKey="work" title={t('tabWork')}>
                            <TodoListCard />
                        </Tab>
                        <Tab eventKey="search" title={t('tabSearch')}>
                            <Tabs
                                defaultActiveKey="registered"
                                variant="pills"
                                className="mb-3"
                                mountOnEnter
                                unmountOnExit
                                fill
                            >
                                <Tab
                                    eventKey="registered"
                                    title={t('subSearchRegistered')}
                                >
                                    <SearchPanel />
                                </Tab>
                                <Tab
                                    eventKey="dates"
                                    title={t('tabDateSearch')}
                                >
                                    <DatePanel />
                                </Tab>
                            </Tabs>
                        </Tab>
                    </Tabs>
                </Col>
            </Row>
        </Container>
    );
}

function App() {
    return (
        <I18nProvider>
            <Main />
        </I18nProvider>
    );
}

export default App;
